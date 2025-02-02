#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import pickle
import duckdb
import os
import time
import psutil

HOST = "0.0.0.0"
PORT = 9000

def handle_client(conn, addr, con):
    """
    Handle single client request:
      1. Receive SQL
      2. Execute SQL
      3. Return results (pickled bytes)
      4. Print and record CPU usage
    """
    # Get current Python process for CPU stats
    process = psutil.Process()
    # Get machine's logical CPU cores (including hyperthreading)
    cpu_count = psutil.cpu_count(logical=True)

    # ---- [1] Record CPU times and wall-clock before receiving SQL request ----
    cpu_times_start = process.cpu_times()
    start_wall_time = time.time()

    try:
        data = conn.recv(4096)
        if not data:
            return

        query = data.decode("utf-8").strip()
        print(f"[Storage] Received query from {addr}:\n  {query}")

        # Fixed logic: set scanned_rows based on query content
        scanned_rows = 0
        lower_q = query.lower()
        if "lineitem" in lower_q:
            scanned_rows += 6001215
        if "part" in lower_q:
            scanned_rows += 200000

        # ---- [2] Execute SQL ----
        query_start = time.time()
        result_data = con.execute(query).fetchall()
        query_end = time.time()
        query_time = query_end - query_start

        print(f"[Storage] Query executed in {query_time:.4f}s, returned rows={len(result_data)}.")
        print(f"[Storage] Hardcoded scanned_rows = {scanned_rows}")

        # ---- [3] Return results to client ----
        payload_dict = {
            'rows': result_data,
            'scanned_rows': scanned_rows,
        }
        payload = pickle.dumps(payload_dict)
        conn.sendall(payload)
        print(f"[Storage] Sent {len(payload)} bytes back to compute.")

    except Exception as e:
        print(f"[Storage] Error while handling request from {addr}: {e}")
    finally:
        # ---- [4] Record CPU times and wall-clock after SQL request ----
        cpu_times_end = process.cpu_times()
        end_wall_time = time.time()

        # Close connection
        conn.close()

        # Calculate CPU time consumed by this request
        user_time_diff = cpu_times_end.user - cpu_times_start.user
        sys_time_diff  = cpu_times_end.system - cpu_times_start.system
        wall_clock_diff = end_wall_time - start_wall_time

        # CPU usage(%) = (CPU time / (wall-clock time x CPU cores)) x 100
        # Remove "x CPU cores" if you want to calculate based on single core
        if wall_clock_diff > 0:
            cpu_usage_pct = (user_time_diff + sys_time_diff) / (wall_clock_diff * cpu_count) * 100.0
        else:
            cpu_usage_pct = 0.0

        print(f"[Storage] CPU usage for this request: {cpu_usage_pct:.2f}% "
              f"(over ~{wall_clock_diff:.3f}s wall-clock)")

def start_storage_server():
    print(f"[Storage] Starting server on {HOST}:{PORT}...")

    # Initialize DuckDB in-memory
    con = duckdb.connect(database=":memory:")

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(5)
    print("[Storage] Listening for connections...")

    while True:
        conn, addr = s.accept()
        print(f"[Storage] Connected by {addr}")
        handle_client(conn, addr, con)

if __name__ == "__main__":
    start_storage_server()
