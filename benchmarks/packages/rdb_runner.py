import os
import time
import pandas as pd
import duckdb
from pathlib import Path
from .runner import Runner
import subprocess
import logging

def drop_caches():
    try:
        # Sync the filesystem
        subprocess.run(['sudo', 'sync'], check=True)

        # Drop caches
        subprocess.run(['sudo', 'sh', '-c', 'echo 3 > /proc/sys/vm/drop_caches'], check=True)

        logging.info("Caches dropped successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"An error occurred: {e}")

class RDBRunner(Runner):
    def __init__(self, args):
        super().__init__(args)
        current_dir = os.path.dirname(__file__)
        parent_dir = os.path.dirname(current_dir)
        self.output_dir = os.path.join(parent_dir, 'RDB', 'output')
        if not os.path.exists(self.output_dir):
            try:
                os.makedirs(self.output_dir, exist_ok=True)
                logging.info(f"Created output directory: {self.output_dir}")
            except OSError as error:
                logging.error(f"Failed to create directory {self.output_dir}: {error}")
            else:
                logging.info(f"Directory {self.output_dir} is ready to use.")
        else:
            logging.debug(f"Directory {self.output_dir} already exists.")

    def run_benchmark_test(self, scale_factors, query, execution_mode, threads):
        for benchmark_item in self.args.benchmark_items.split(','):
            results = []
        sf = scale_factors
        duckdb_file_path = os.path.join(self.output_dir, f'sf{sf}')
        if not os.path.exists(duckdb_file_path):
            duckdb_file_path = os.path.join(self.output_dir, f'sf{sf}')
            with duckdb.connect(database=duckdb_file_path, read_only=False) as conn:
                conn.execute("LOAD tpch")
                conn.execute(f"CALL dbgen(sf={sf})")
                logging.info(f"Data generated for SF={sf} in DuckDB database at {duckdb_file_path}")

        with duckdb.connect(database=duckdb_file_path, read_only=True) as conn:
            
            query_name = f"Q{int(query)}"
            cmd = f"PRAGMA tpch({query});"
            if execution_mode == "cold":
                conn.close()
                conn = duckdb.connect(database=duckdb_file_path, read_only=True)
                # Simulate a cold start by reopening the connection
                drop_caches()
                if threads != "0":
                    conn.execute(f"PRAGMA threads={threads};")
                threads_setting = conn.execute("SELECT current_setting('threads')").fetchone()
                # print(threads_setting[0])
                
                start_time = time.time()
                conn.execute(cmd)
                end_time = time.time()

                run_time = end_time - start_time
                results.append({
                    'Scale Factor': sf,
                    'Query': query_name,
                    'Execution Mode': execution_mode,
                    'Threads': threads, 
                    'Run Time (s)': run_time
                })
            elif execution_mode == "hot":
                conn.close()
                conn = duckdb.connect(database=duckdb_file_path, read_only=True)
                # Simulate a cold start by reopening the connection
                drop_caches()
                if threads != "0":
                    conn.execute(f"PRAGMA threads={threads};")
                threads_setting = conn.execute("SELECT current_setting('threads')").fetchone()
                # print(threads_setting[0])
                run_times = []
                for i in range(4):
                    start_time = time.time()
                    conn.execute(cmd)
                    end_time = time.time()
                    if i > 0:  # Ignore the first run
                        run_times.append(end_time - start_time)
                
                run_time = sum(run_times) / len(run_times)
                results.append({
                    'Scale Factor': sf,
                    'Query': query_name,
                    'Execution Mode': execution_mode,
                    'Threads': threads, 
                    'Run Time (s)': run_time
                })

        # Calculate average run time for all queries
        results_df = pd.DataFrame(results)

        results_csv_path = os.path.join(self.output_dir, 'results.csv')
        # Check if the file already exists and append if it does
        if os.path.exists(results_csv_path):
            existing_df = pd.read_csv(results_csv_path)
            results_df = pd.concat([existing_df, results_df], ignore_index=True)
        results_df.to_csv(results_csv_path, index=False)
        logging.info(f"Running RDB benchmark for {benchmark_item} with scale factors {scale_factors}, query {query}, execution mode {execution_mode}")
