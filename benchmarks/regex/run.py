import argparse
import subprocess
import sys
import json
import os
from datetime import datetime
import io
import subprocess
import re
import csv
import zlib_ng
from zlib_ng import gzip_ng_threaded, gzip_ng
import zlib
from time import perf_counter_ns

VALID_ITEMS = ['default', 'simd', 'threading', 'doca']

def write_results(type, bs, threads, throughput_mbps):
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'output', 'regex')
    os.makedirs(output_dir, exist_ok=True)
    output_filename = "results.csv"
    result_file = os.path.join(output_dir, output_filename)
    if not os.path.exists(result_file):
        # write the columns header
        fp = open(result_file, 'w')
        writer = csv.writer(fp)
        writer.writerow(["type", "block size", "threads", "throughput (MB/s)"])
    else:
        fp = open(result_file, 'a')
        writer = csv.writer(fp)
        

    # Write the results
    writer.writerow([type, str(bs / 1024) + 'K', threads, throughput_mbps])
    fp.close()

this_dir = os.path.dirname(os.path.realpath(__file__))
doca_dir = os.path.join(this_dir, 'doca_regex')
build_dir = os.path.join(doca_dir, 'build')
hs_dir = os.path.join(this_dir, 'vectorscan')

# def default_regex(data_size, threads):
#     # hs <n_threads> <input_file> <re>
#     output = subprocess.run(['hs', 1, os.path.join(hs_dir, 'o_comment.txt'), r"[\w\s]+special[\w\s]+requests[\w\s]*\n"], capture_output=True, text=True)
#     found = re.findall(r"duration: (.+)", output.stdout)
#     print(found[0])
#     completion_time = float(found[0])
#     throughput_mbps = float(data_size) / completion_time / 1024 / 1024
#     print(f"Throughput - default: {throughput_mbps} MB/s")
#     write_results('default', data_size, threads, throughput_mbps)

def simd_regex(data_size, threads):
    # hs <n_threads> <input_file> <re>
    output = subprocess.run(['hs-simd', threads, os.path.join(hs_dir, f'{data_size}.txt'), r"[\w\s]+special[\w\s]+requests[\w\s]*\n"],
                            capture_output=True, text=True, cwd=this_dir)
    found = re.findall(r"duration \(ns\): (.+)", output.stdout)
    print(found[0])
    completion_time = float(found[0])
    time_ms = completion_time / 1000000
    # throughput_mbps = float(data_size) / completion_time / 1024 / 1024
    # print(f"Throughput - simd: {throughput_mbps} MB/s")
    write_results('simd', data_size, threads, time_ms)

def threading_regex(data_size, threads):
    # hs <n_threads> <input_file> <re>
    output = subprocess.run(['hs', threads, os.path.join(hs_dir, f'{data_size}.txt'), r"[\w\s]+special[\w\s]+requests[\w\s]*\n"],
                            capture_output=True, text=True, cwd=this_dir)
    found = re.findall(r"duration \(ns\): (.+)", output.stdout)
    print(found[0])
    completion_time = float(found[0])
    time_ms = completion_time / 1000000
    # throughput_mbps = float(data_size) / completion_time / 1024 / 1024
    # print(f"Throughput - threading: {throughput_mbps} MB/s")
    write_results('threading', data_size, threads, time_ms)

def doca_regex(data_size):
    rules_file = os.path.join(doca_dir, 'rxpc', 'rules.rof2.binary')
    txt_file = os.path.join(hs_dir, 'o_comment.txt')
    # TODO:  data_size
    output = subprocess.run(f"sudo ./doca_regex/doca_regex -p 03:00.0 -r {rules_file} -d {txt_file}", shell=True, capture_output=True, text=True)
    found = re.findall(r"total = (.+)", output.stdout)
    print(found[0])
    completion_time = float(found[0])
    time_ms = completion_time / 1000000
    # throughput_mbps = float(data_size) / completion_time / 1024 / 1024
    # print(f"Throughput - doca: {throughput_mbps} MB/s")
    write_results('doca', data_size, 0, time_ms)

def main():
    parser = argparse.ArgumentParser(description='Run regex benchmark')
    parser.add_argument('--benchmark_items', help='Comma-separated list of benchmark items')
    parser.add_argument('--data_size', type=str, default='4K', help='input text data size (KB)')
    parser.add_argument('--threads', type=int, default=1, help='Number of threads')
    args, _ = parser.parse_known_args()

    items = args.benchmark_items.split(',')
    data_size = args.data_size
    for item in items:
        # if item == 'default':
        #     default_regex(data_size, args.threads)
        if item == 'simd':
            simd_regex(data_size, args.threads)
        elif item == 'threading':
            threading_regex(data_size, args.threads)
        elif item == 'doca':
            doca_regex(data_size)
        else:
            print(f"Invalid item: {item}")

if __name__ == '__main__':  
    main()