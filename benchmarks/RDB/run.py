import os
import sys

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

if base_dir not in sys.path:
    sys.path.append(base_dir)
    
from benchmarks.packages.rdb_parser import RDBParser
from benchmarks.packages.rdb_runner import RDBRunner

if __name__ == '__main__':
    rdb_parser = RDBParser()
    args = rdb_parser.parse_arguments()
    rdb_runner = RDBRunner(args)
    rdb_runner.run_benchmark_test(args.scale_factors, args.query, args.execution_mode, args.threads)
