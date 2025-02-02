#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import os
import time
import threading

HOST = "0.0.0.0"
PORT = 9000
BUFFER_SIZE = 16 * 1024 * 1024  # 16MB buffer
STORAGE_DATA_DIR = "/"

def read_line(conn):

    buf = b""
    while True:
        chunk = conn.recv(1)
        if not chunk:  
            break
        if chunk == b'\n': 
            break
        buf += chunk
    return buf.decode('utf-8').strip()

def handle_client(conn, addr):
    try:
    
        conn.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, BUFFER_SIZE)
        conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    
        num_files = int(read_line(conn))
        print(f"[Storage] Client {addr} requested {num_files} files")

        for _ in range(num_files):
            fpath_line = read_line(conn)
            if not fpath_line:
                conn.sendall(b"-1\n")
                continue

            full_path = os.path.join(STORAGE_DATA_DIR, fpath_line.lstrip("./"))
            print(f"[Storage] Sending file: {full_path}")

            if not os.path.isfile(full_path):
                conn.sendall(b"-1\n")
                print(f"[Storage] File not found: {full_path}")
                continue

            file_size = os.path.getsize(full_path)
            conn.sendall(f"{file_size}\n".encode('utf-8'))

            send_start = time.time()
            bytes_sent = 0

            with open(full_path, "rb", buffering=BUFFER_SIZE) as f_in:
                while bytes_sent < file_size:
                    chunk_size = min(BUFFER_SIZE, file_size - bytes_sent)
                    data = f_in.read(chunk_size)
                    if not data:
                        break
                    conn.sendall(data)
                    bytes_sent += len(data)

            send_time = time.time() - send_start
            speed_mbps = (bytes_sent / 1024 / 1024) / send_time if send_time > 0 else 0

            print(f"[Storage] Sent file: {full_path}")
            print(f"[Storage] Size: {bytes_sent:,} bytes")
            print(f"[Storage] Time: {send_time:.2f}s")
            print(f"[Storage] Speed: {speed_mbps:.2f} MB/s")

    except Exception as e:
        print(f"[Storage] Error handling {addr}: {e}")
    finally:
        conn.close()

def start_storage_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    

    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, BUFFER_SIZE)
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    
    s.bind((HOST, PORT))
    s.listen(10)
    print(f"[Storage] Listening on {HOST}:{PORT}")

    while True:
        conn, addr = s.accept()
        print(f"[Storage] New connection from {addr}")
        threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == "__main__":
    start_storage_server()
