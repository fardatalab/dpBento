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

VALID_ITEMS = ['default', 'threaded-single', 'single', 'threading', 'doca']

def write_results(type, data_size, bs, threads, latency, operation='compression'):
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'output', operation)
    os.makedirs(output_dir, exist_ok=True)
    output_filename = "results.csv"
    result_file = os.path.join(output_dir, output_filename)
    if not os.path.exists(result_file):
        # write the columns header
        fp = open(result_file, 'w')
        writer = csv.writer(fp)
        writer.writerow(["type", "data_size", "block size", "threads", "latency (ms)"])
    else:
        fp = open(result_file, 'a')
        writer = csv.writer(fp)
        

    # Write the results
    writer.writerow([type, data_size, str(bs / 1024) + 'K', threads, latency])
    fp.close()

def create_tmp_file(data_size: str):
    root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
    this_dir = os.path.dirname(os.path.realpath(__file__))
    txt_file = os.path.join(this_dir, f'256.txt')
    build_dir = os.path.join(this_dir, 'build')
    os.makedirs(build_dir, exist_ok=True)
    tmp_file = os.path.join(this_dir, f'tmp.txt')
    subprocess.run(['cp', txt_file, tmp_file])
    subprocess.run(['truncate', '-s', data_size, tmp_file], cwd=this_dir, check=True)
    return tmp_file

def default_compress(data_size, block_size, threads):
    fname = create_tmp_file(data_size)
    txt = open(fname, 'rb').read()
    start = perf_counter_ns()
    buf = zlib.compress(txt)
    end = perf_counter_ns()
    elapsed_ms = (end - start) / 1_000_000

    write_results('default', data_size, block_size, 1, elapsed_ms)

def threaded_compress_single(data_size, block_size, threads):
    buf = io.BytesIO()
    fname = create_tmp_file(data_size)
    txt = open(fname, 'rb').read()
    
    # start = perf_counter_ns()
    fp = gzip_ng_threaded.open(buf, 'w', threads=1, block_size=block_size)
    start = perf_counter_ns()
    r=fp.write(txt)
    fp.flush()
    end = perf_counter_ns()

    elapsed_ms = (end - start) / 1_000_000

    # # get file size
    # fsize = os.path.getsize(fname)
    # print('fsize:', fsize)
    # throughput = fsize / elapsed_ms / 1024
    # print(f"SIMD throughput: {throughput} MB/s")
    write_results('threded-single', data_size, block_size, 1, elapsed_ms)

def compress_single(data_size, block_size, threads):
    buf = io.BytesIO()
    fname = create_tmp_file(data_size)
    txt = open(fname, 'rb').read()
    
    # start = perf_counter_ns()
    fp = gzip_ng_threaded.open(buf, 'w', threads=0, block_size=block_size)
    start = perf_counter_ns()
    r=fp.write(txt)
    fp.flush()
    end = perf_counter_ns()

    elapsed_ms = (end - start) / 1_000_000

    # # get file size
    # fsize = os.path.getsize(fname)
    # print('fsize:', fsize)
    # throughput = fsize / elapsed_ms / 1024
    # print(f"SIMD throughput: {throughput} MB/s")
    write_results('single', data_size, block_size, 1, elapsed_ms)

def threading_compress(data_size, block_size, threads):
    buf = io.BytesIO()
    # fname = os.path.join(os.path.dirname(os.path.realpath(__file__)), '256.txt')
    fname = create_tmp_file(data_size)
    txt = open(fname, 'rb').read()
    
    # start = perf_counter_ns()
    fp = gzip_ng_threaded.open(buf, 'w', threads=threads, block_size=block_size)
    start = perf_counter_ns()
    fp.write(txt)
    fp.flush()
    end = perf_counter_ns()

    elapsed_ms = (end - start) / 1_000_000
    
    write_results('threading (max)', data_size, block_size, threads, elapsed_ms)


############## decompress ####################
def threaded_decompress_single(data_size, block_size, threads):
    data_name =f'{data_size}.txt.gz'
    this_dir = os.path.dirname(os.path.realpath(__file__))
    fname = os.path.join(this_dir, data_name)
    buf = io.BytesIO(open(fname, 'rb').read())
    
    # start = perf_counter_ns()
    fp = gzip_ng_threaded.open(buf, 'rb', threads=1, block_size=block_size)
    start = perf_counter_ns()
    r=fp.read()
    fp.flush()
    end = perf_counter_ns()

    elapsed_ms = (end - start) / 1_000_000

    # # get file size
    # fsize = os.path.getsize(fname)
    # print('fsize:', fsize)
    # throughput = fsize / elapsed_ms / 1024
    # print(f"SIMD throughput: {throughput} MB/s")
    write_results('threaded-single', data_size, block_size, 1, elapsed_ms, operation='decompression')

def decompress_single(data_size, block_size, threads):
    data_name =f'{data_size}.txt.gz'
    this_dir = os.path.dirname(os.path.realpath(__file__))
    fname = os.path.join(this_dir, data_name)
    buf = io.BytesIO(open(fname, 'rb').read())

    fp = gzip_ng_threaded.open(buf, 'rb', threads=0, block_size=block_size)
    start = perf_counter_ns()
    r=fp.read()
    fp.flush()
    end = perf_counter_ns()

    elapsed_ms = (end - start) / 1_000_000

    # # get file size
    # fsize = os.path.getsize(fname)
    # print('fsize:', fsize)
    # throughput = fsize / elapsed_ms / 1024
    # print(f"SIMD throughput: {throughput} MB/s")
    write_results('single', data_size, block_size, 1, elapsed_ms, operation='decompression')

def threading_decompress(data_size, block_size, threads):
    data_name =f'{data_size}.txt.gz'
    this_dir = os.path.dirname(os.path.realpath(__file__))
    fname = os.path.join(this_dir, data_name)
    buf = io.BytesIO(open(fname, 'rb').read())
    
    # start = perf_counter_ns()
    fp = gzip_ng_threaded.open(buf, 'rb', threads=threads, block_size=block_size)
    start = perf_counter_ns()
    fp.read()
    fp.flush()
    end = perf_counter_ns()

    elapsed_ms = (end - start) / 1_000_000
    
    write_results('threading (max)', data_size, block_size, threads, elapsed_ms, operation='decompression')

def doca_compress(data_size: str):
    root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
    this_dir = os.path.dirname(os.path.realpath(__file__))
    txt_file = os.path.join(this_dir, f'256.txt')
    build_dir = os.path.join(this_dir, 'build')
    exec_name = os.path.join(build_dir, 'doca_compress')
    output_dir = os.path.join(root_dir, 'output', 'compress')
    result_file = os.path.join(output_dir, 'doca_result.csv')
    tmp_file = create_tmp_file(data_size)

    os.makedirs(output_dir, exist_ok=True)
    output = subprocess.run([exec_name, '-p', "03:00.0", '-m', 'compress', '-f', tmp_file, '-o', 'rub.out'],
                            cwd=build_dir, capture_output=True, text=True).stdout
    # total = 0.05553569
    found = re.findall(r"total = (.+)", output)
    elapsed_s = float(found[0])
    # get file size
    fsize = os.path.getsize(tmp_file)
    # print('fsize:', fsize)
    throughput = fsize / elapsed_s / 1024 / 1024
    print(f"DOCA throughput: {throughput} MB/s")
    write_results('doca', data_size, data_size, 0, elapsed_s * 1000)

def main():
    parser = argparse.ArgumentParser(description='Run compression benchmark')
    parser.add_argument('--benchmark_items', help='Comma-separated list of benchmark items')
    parser.add_argument('--operation', type=str, default='compression', help='Operation type')
    parser.add_argument('--block_size', type=int, default=1, help='Block size in KB')
    parser.add_argument('--data_size', type=str, default='4K', help='Data size')
    parser.add_argument('--threads', type=int, default=-1, help='Number of threads')
    args, _ = parser.parse_known_args()

    items = args.benchmark_items.split(',')
    block_size = args.block_size * 1024
    data_size = args.data_size
    for item in items:
        if args.operation == 'compress':
            if item == 'default':
                default_compress(data_size, block_size, args.threads)
            elif item == 'threaded-single':
                threaded_compress_single(data_size, block_size, args.threads)
            elif item == 'single':
                compress_single(data_size, block_size, args.threads)
            elif item == 'threading':
                threading_compress(data_size, block_size, args.threads)
            elif item == 'doca':
                doca_compress(data_size)
            else:
                print(f"Invalid item: {item}")
        elif args.operation == 'decompress':
            if item == 'threaded-single':
                threaded_decompress_single(data_size, block_size, args.threads)
            elif item == 'single':
                decompress_single(data_size, block_size, args.threads)
            elif item == 'threading':
                threading_decompress(data_size, block_size, args.threads)
            elif item == 'doca':
                print(f"DOCA decompression not implemented yet")
            else:
                print(f"Invalid item: {item}")
        else:
            print(f"Invalid operation: {args.operation}")

if __name__ == '__main__':  
    main()