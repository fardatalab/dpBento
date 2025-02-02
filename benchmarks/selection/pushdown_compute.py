#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import pickle
import sys
import time
import os
import psutil

STORAGE_HOST = "192.168.1.100"
STORAGE_PORT = 9000

def send_query_and_get_result(query: str):
    """
    1) Connect to Storage
    2) Send query
    3) Receive pickled result (payload_dict)
    4) Return (result_rows, scanned_rows, data_time, data_size, server_query_time)
       - data_time: network time
       - data_size: total bytes from network
       - server_query_time: from payload_dict['query_time'] if present
    """
    start_time = time.time()
    received_data = b""

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((STORAGE_HOST, STORAGE_PORT))

        # Send SQL
        s.sendall(query.encode("utf-8"))

        # Receive returned data
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            received_data += chunk

    end_time = time.time()
    data_time = end_time - start_time  # network transfer + server waiting time
    data_size = len(received_data)     # total bytes from network

    # Unpack data
    payload_dict = pickle.loads(received_data)
    result_rows = payload_dict['rows']
    scanned_rows = payload_dict.get('scanned_rows', 0)

    # Get server SQL execution time if returned by Storage
    server_query_time = payload_dict.get('query_time', 0.0)

    return result_rows, scanned_rows, data_time, data_size, server_query_time

def main():
    # Get current process object
    process = psutil.Process()

    # Record CPU times and wall-clock at script start
    cpu_times_start = process.cpu_times()  # (user, system, children_user, children_system, iowait)
    overall_start = time.time()

    # List of query files to execute
    query_files = [f"query6_{i}.sql" for i in range(1, 11)]

    total_scanned = 0
    total_rows_returned = 0
    total_data_time = 0.0
    total_data_size = 0
    total_query_exec_time = 0.0

    executed_count = 0

    # Get number of CPU cores (logical CPUs)
    num_cpus = psutil.cpu_count(logical=True)

    for qf in query_files:
        if not os.path.exists(qf):
            print(f"[Compute] Query file {qf} does not exist. Skipping.")
            continue

        with open(qf, "r", encoding="utf-8") as f:
            query = f.read().strip()

        print(f"\n[Compute] ===== Executing {qf} =====")

        # ---- Record CPU times & wall-clock before single query execution ----
        single_query_cpu_start = process.cpu_times()
        single_query_wall_start = time.time()

        # Execute query
        result_rows, scanned_rows, data_time, data_size, server_query_time = send_query_and_get_result(query)

        # ---- Record CPU times & wall-clock after single query execution ----
        single_query_cpu_end = process.cpu_times()
        single_query_wall_end = time.time()

        # Calculate CPU usage for single query
        user_diff = single_query_cpu_end.user - single_query_cpu_start.user
        sys_diff = single_query_cpu_end.system - single_query_cpu_start.system
        query_wall_diff = single_query_wall_end - single_query_wall_start

        # Note: Usage = (Total CPU time / (wall-clock * CPU cores)) * 100
        # If you only want to see single core usage, don't multiply by num_cpus
        single_query_cpu_usage_pct = (user_diff + sys_diff) / (query_wall_diff * num_cpus) * 100.0

        # Update summary
        row_count = len(result_rows)
        total_rows_returned += row_count
        total_scanned += scanned_rows

        total_data_time += data_time
        total_data_size += data_size
        total_query_exec_time += server_query_time
        executed_count += 1

        print(f"[Compute] {qf} => Returned {row_count} rows, scanned={scanned_rows}, "
              f"data_time={data_time:.4f}s, data_size={data_size}, server_time={server_query_time:.4f}s")
        print(f"[Compute] Single-query CPU usage: {single_query_cpu_usage_pct:.2f}% "
              f"(measured over ~{query_wall_diff:.3f} sec)")

        if row_count > 0:
            print("[Compute] Sample first row:", result_rows[0])

    # ---- Record CPU times & wall-clock at script end ----
    cpu_times_end = process.cpu_times()
    overall_end = time.time()

    # Calculate average CPU usage over entire script runtime
    total_user_time = cpu_times_end.user - cpu_times_start.user
    total_sys_time = cpu_times_end.system - cpu_times_start.system
    overall_wall_time = overall_end - overall_start

    # Calculate usage using the same formula
    overall_cpu_usage_pct = (total_user_time + total_sys_time) / (overall_wall_time * num_cpus) * 100.0

    # Print Summary
    print("\n[Compute] ===================== Summary =====================")
    print(f"[Compute] Total queries executed   : {executed_count}")
    print(f"[Compute] Total scanned rows       : {total_scanned}")
    print(f"[Compute] Total returned rows      : {total_rows_returned}")
    print(f"[Compute] Total data transfer time : {total_data_time:.4f}s")
    print(f"[Compute] Total data transfer size : {total_data_size} bytes")
    print(f"[Compute] Overall time (wall-clock): {overall_wall_time:.4f}s")
    print(f"[Compute] Average CPU usage        : {overall_cpu_usage_pct:.2f}%")
    if overall_wall_time > 0 and total_scanned > 0:
        throughput = total_scanned / overall_wall_time
        print(f"[Compute] Overall throughput       : {throughput:.1f} rows/sec (scanned).")
    else:
        print("[Compute] overall_time=0 or total_scanned=0 => cannot compute throughput.")

if __name__ == "__main__":
    main()
