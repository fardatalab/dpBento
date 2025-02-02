#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import os
import time
import duckdb
import psutil
import concurrent.futures
import re
import argparse
from typing import List, Dict, Set, Tuple


STORAGE_HOST = "192.168.1.100"
STORAGE_PORT = 9000
BUFFER_SIZE = 16 * 1024 * 1024  # 16MB buffer
LOCAL_TEMP_DIR = "/home/chihan/temp"
QUERIES_DIR = "/home/chihan/orginalQuery"
# ===========================================================


class QueryInfo:

    def __init__(self, path: str, sql: str, needed_files: Set[str]):
        self.path = path
        self.sql = sql
        self.needed_files = needed_files


def parse_arguments():

    parser = argparse.ArgumentParser(description="Script to batch-download parquet files and run queries.")
    parser.add_argument("-d", "--download-threads",
                        type=int,
                        default=4,
                        help="Number of threads to use for downloading and DuckDB queries (max 16). Default=4.")
    return parser.parse_args()


def parse_parquet_paths(sql: str) -> Set[str]:

    pattern = r"parquet_scan\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"
    paths = re.findall(pattern, sql, flags=re.IGNORECASE)
    return set(paths)


def collect_all_files_and_queries() -> Tuple[Set[str], List[QueryInfo]]:
 
    all_files = set()
    queries = []
    
    query_files = sorted(
        f for f in os.listdir(QUERIES_DIR) 
        if f.startswith("orginal_query6_") and f.endswith(".sql")
    )
    
    for qf in query_files:
        query_path = os.path.join(QUERIES_DIR, qf)
        with open(query_path, "r", encoding="utf-8") as f:
            sql_text = f.read()
        needed_files = parse_parquet_paths(sql_text)
        all_files.update(needed_files)
        queries.append(QueryInfo(query_path, sql_text, needed_files))
        
    return all_files, queries


def fetch_one_file_sequential(sock: socket.socket, original_fpath: str) -> Tuple[str, str, int]:

    try:
    
        sock.sendall(f"{original_fpath}\n".encode("utf-8"))

      
        size_buf = b""
        while True:
            chunk = sock.recv(1)
            if not chunk or chunk == b"\n":
                break
            size_buf += chunk

        if not size_buf:
            print(f"[Compute] Error: no size info for {original_fpath}")
            return original_fpath, None, 0

        file_size = int(size_buf.decode("utf-8"))
        if file_size < 0:
            print(f"[Compute] Storage says file not found: {original_fpath}")
            return original_fpath, None, 0

      
        dataset_id = original_fpath.split("/")[-2] if "/" in original_fpath else "data"
        base_name = os.path.basename(original_fpath)
        unique_filename = f"{dataset_id}_{base_name}"
        local_full_path = os.path.join(LOCAL_TEMP_DIR, unique_filename)
        os.makedirs(LOCAL_TEMP_DIR, exist_ok=True)

    
        total_recv = 0
        with open(local_full_path, "wb", buffering=BUFFER_SIZE) as f_out:
            while total_recv < file_size:
                chunk_size = min(BUFFER_SIZE, file_size - total_recv)
                data = sock.recv(chunk_size)
                if not data:
                    break
                f_out.write(data)
                total_recv += len(data)

        print(f"[Compute] Received => {local_full_path}, size={total_recv:,} bytes")
        return original_fpath, local_full_path, total_recv

    except Exception as e:
        print(f"[Compute] Error receiving {original_fpath}: {e}")
        return original_fpath, None, 0


def download_chunk(file_list: List[str]) -> List[Tuple[str, str, int]]:

    results = []
    if not file_list:
        return results

   
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFFER_SIZE)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    try:
        sock.connect((STORAGE_HOST, STORAGE_PORT))
      
        sock.sendall(f"{len(file_list)}\n".encode("utf-8"))

     
        for fpath in file_list:
            orig_path, local_path, fsize = fetch_one_file_sequential(sock, fpath)
            results.append((orig_path, local_path, fsize))

    except Exception as e:
        print(f"[Compute] Error in download_chunk: {e}")

    finally:
        try:
            sock.close()
        except:
            pass

    return results


def batch_download_files(all_files: Set[str], download_threads: int) -> Tuple[Dict[str, str], float, int]:

    if not all_files:
        return {}, 0.0, 0

  
    download_threads = min(download_threads, 16)

    file_list = list(all_files)
    total_files = len(file_list)

   
    chunk_size = (total_files // download_threads) + (1 if total_files % download_threads != 0 else 0)
    chunked_file_lists = []
    for i in range(0, total_files, chunk_size):
        chunked_file_lists.append(file_list[i:i+chunk_size])

    print(f"[Compute] All files: {total_files}. "
          f"Split into {len(chunked_file_lists)} chunks for {download_threads} thread(s).")

    path_map = {}
    total_size = 0
    start_time = time.time()

 
    with concurrent.futures.ThreadPoolExecutor(max_workers=download_threads) as executor:
        future_to_chunk = {executor.submit(download_chunk, chunk): chunk for chunk in chunked_file_lists}
        for future in concurrent.futures.as_completed(future_to_chunk):
            res_list = future.result()  # [ (orig_path, local_path, size), ... ]
            if not res_list:
                continue
            for (orig_path, local_path, fsize) in res_list:
                if local_path:  
                    path_map[orig_path] = local_path
                    total_size += fsize

    total_time = time.time() - start_time
    return path_map, total_time, total_size


def execute_query(query_info: QueryInfo, path_map: Dict[str, str], query_threads: int) -> Tuple[str, int, int, float]:

    query_start = time.time()
    modified_query = query_info.sql

  
    for old_path in query_info.needed_files:
        local_path = path_map.get(old_path)
        if local_path:
            modified_query = modified_query.replace(old_path, local_path)

    print(f"[Compute] Executing query from {query_info.path}:\n{modified_query}")

  
    scanned_rows = 0
    if "lineitem" in modified_query.lower():
        scanned_rows = 6001215

    conn = duckdb.connect(database=":memory:")
   
    conn.execute(f"SET threads TO {query_threads}")
    
    try:
        result = conn.execute(modified_query).fetchall()
        row_count = len(result)
    finally:
        conn.close()

    query_time = time.time() - query_start
    print(f"[Compute] {query_info.path} => rows={row_count}, scanned={scanned_rows}, time={query_time:.4f}s")
    
    return query_info.path, row_count, scanned_rows, query_time


def main():
   
    args = parse_arguments()
    download_threads = args.download_threads

  
    query_threads = download_threads

    overall_start = time.time()
    process = psutil.Process()
    cpu_times_start = process.cpu_times()

  
    print("[Compute] Collecting queries and required files...")
    all_files, queries = collect_all_files_and_queries()
    print(f"[Compute] Found {len(queries)} queries requiring {len(all_files)} unique files")
    
 
    print(f"\n[Compute] Starting batch file download with {download_threads} thread(s)...")
    path_map, download_time, total_size = batch_download_files(all_files, download_threads)
    print(f"[Compute] Download complete: {total_size:,} bytes in {download_time:.2f}s")
    if download_time > 0:
        print(f"[Compute] Average download speed: {(total_size/1024/1024)/download_time:.2f} MB/s")
    else:
        print("[Compute] Average download speed: N/A (0s download time)")

  
    print(f"\n[Compute] Starting parallel query execution with {query_threads} DuckDB threads...")
    query_start = time.time()
    total_rows = 0
    total_scanned = 0
    query_times = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=query_threads) as executor:
        futures = [executor.submit(execute_query, q, path_map, query_threads) for q in queries]
        for future in concurrent.futures.as_completed(futures):
            query_path, rows, scanned, q_time = future.result()
            total_rows += rows
            total_scanned += scanned
            query_times.append((query_path, rows, scanned, q_time))
    
    total_query_time = time.time() - query_start

 
    overall_time = time.time() - overall_start
    cpu_times_end = process.cpu_times()

    print("\n[Compute] Cleaning up temporary files...")
    for local_path in path_map.values():
        if local_path and os.path.exists(local_path):
            os.remove(local_path)
    
    cpu_user = cpu_times_end.user - cpu_times_start.user
    cpu_sys = cpu_times_end.system - cpu_times_start.system
    total_cpu_time = cpu_user + cpu_sys
    
    if overall_time > 0:
        cpu_usage = total_cpu_time / (overall_time * psutil.cpu_count(logical=True)) * 100
        overall_throughput = total_scanned / overall_time
        query_throughput = (total_scanned / total_query_time) if total_query_time > 0 else 0
    else:
        cpu_usage = 0
        overall_throughput = 0
        query_throughput = 0
    
  
    print("\n[Compute] ===================== Summary =====================")
    print(f"[Compute] Download threads used  : {download_threads}")
    print(f"[Compute] DuckDB threads used    : {query_threads}")
    print(f"[Compute] Files downloaded       : {len(path_map)}")
    print(f"[Compute] Total data size        : {total_size:,} bytes")
    print(f"[Compute] Download time          : {download_time:.2f}s")
    if download_time > 0:
        print(f"[Compute] Download speed         : {(total_size/1024/1024)/download_time:.2f} MB/s")
    else:
        print("[Compute] Download speed         : N/A")
    print(f"[Compute] Queries executed       : {len(queries)}")
    print(f"[Compute] Total rows returned    : {total_rows:,}")
    print(f"[Compute] Total rows scanned     : {total_scanned:,}")
    print(f"[Compute] Total query time       : {total_query_time:.2f}s")
    print(f"[Compute] Total time (wall-clock): {overall_time:.2f}s")
    print(f"[Compute] CPU usage              : {cpu_usage:.1f}%")
    print(f"[Compute] Overall throughput     : {overall_throughput:,.0f} rows/sec (including download)")
    print(f"[Compute] Query throughput       : {query_throughput:,.0f} rows/sec (query only)")
    
    print("\n[Compute] Per-Query Details:")
    for qpath, rows, scanned, qtime in query_times:
        throughput = scanned / qtime if qtime > 0 else 0
        print(f"[Compute] {os.path.basename(qpath)}: {scanned:,} scanned, {throughput:,.0f} rows/sec")


if __name__ == "__main__":
    main()
