import os
import argparse
import subprocess
#import json
import logging
import glob

def parse_arguments():
    parser = argparse.ArgumentParser(description="Run BTree benchmark.")
    parser.add_argument('--num_threads', type=int, default=0, help='Number of threads to run YCSB with. 0 means max')
    parser.add_argument('--num_records', type=str, default="5000000", help="number of records to store in the db")
    parser.add_argument('--num_operations_per_thread', type=int, default="16777216", help="numbers of operations to run per thread")
    parser.add_argument('--lmdb_mapsize', type=str, default="10737418240", help="amount of space for lmdb's map")
    parser.add_argument('--db_path', type=str, default="/tmp/ycsb-lmdb", help="backing file for lmdb")
    parser.add_argument('--metrics', type=str, help="ignore")
    parser.add_argument('--benchmark_items', type=str, help="ignore")

    return parser.parse_args()

def run_command(command, check=True, shell=False, capture_output=False):
    """Run a shell command."""
    logging.info(f"Running command: {' '.join(command)}")
    out = subprocess.run(command, check=check, shell=shell, capture_output=True)
    return out
    if capture_output:
        return out
    return ""

def main():
    args = parse_arguments()
    if args.num_threads == 0:
        args.num_threads = os.cpu_count()
    benchmark_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(benchmark_dir + "/YCSB-cpp/")
    lmdb_config = ["lmdb.dbpath="+args.db_path+"\n", "lmdb.mapsize="+args.lmdb_mapsize+"\n"]
    with open("./lmdb/lmdb.properties", "r") as f:
        lines = f.readlines()
    lines[:2] = lmdb_config
    with open("./lmdb/lmdb.properties", "w") as f:
        f.writelines(lines)
    out = run_command(["./ycsb", "-load", "-run", "-db", "lmdb", "-P", "workloads/workloadc", 
                 "-P", "lmdb/lmdb.properties", "-p", "threadcount=" + str(args.num_threads),
                 "-p" "recordcount=" + str(args.num_records), "-p", 
                 "operationcount=" + str(args.num_operations_per_thread * args.num_threads) , "-s" ], capture_output=True)

    os.chdir("../")
    results_file_path = os.path.join(benchmark_dir, "results.csv")
    with open(results_file_path, "a") as output_file:
        output_file.write(str(args.num_threads) + "," + args.num_records + "," + str(args.num_operations_per_thread * args.num_threads) + ",")
        throughput = str(out.stdout.splitlines()[-1]).split(" ")[-1]
        output_file.write(throughput + "\n")
    run_command(["rm", "-r", args.db_path])        
if __name__ == '__main__':
    main()
