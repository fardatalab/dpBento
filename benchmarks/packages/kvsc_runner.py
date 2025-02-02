import os
import time
import pandas as pd
from pathlib import Path
from .runner import Runner
import subprocess
import logging

READ = 0
UPDATE = 1
INSERT = 2
SCAN = 3

class KVSRunner(Runner):
    def __init__(self, args, dir):
        super().__init__(args)
        current_dir = os.path.dirname(__file__)
        parent_dir = os.path.dirname(current_dir)
        self.output_dir = os.path.join(parent_dir, dir, 'output')
        if not os.path.exists(self.output_dir):
            try:
                os.makedirs(self.output_dir, exist_ok=True)
                logging.info(f"Created output directory: {self.output_dir}")
            except OSError as error:
                logging.error(f"Failed to create directory {self.output_dir}: {error}")
            else:
                logging.info(f"Directory {self.output_dir} is ready to use.")
        else:
            logging.info(f"Directory {self.output_dir} already exists.")

    def get_unique_filename(self, directory, base_name):
        """Generate a unique filename by incrementing a counter."""
        base, ext = os.path.splitext(base_name)
        counter = 1
        unique_name = f"{base}{counter}{ext}"
        
        while os.path.exists(os.path.join(directory, unique_name)):
            counter += 1
            unique_name = f"{base}{counter}{ext}"
        
        return os.path.join(directory, unique_name)

    def generate_workload_config(self, operation_size, operation_type, data_distribution_type):
        """Generate the workload configuration file."""
        config_content = f"""
        recordcount={operation_size}
        operationcount={operation_size}
        workload=site.ycsb.workloads.CoreWorkload

        readallfields=true

        readproportion={operation_type[READ]}
        updateproportion={operation_type[UPDATE]}
        insertproportion={operation_type[INSERT]}
        scanproportion={operation_type[SCAN]}

        requestdistribution={data_distribution_type}
        """
        config_file = self.get_unique_filename(self.output_dir, 'workload_generated.txt')
        with open(config_file, 'w') as f:
            f.write(config_content)
        return config_file

    def run_benchmark_test(self, operation_size, operation_type, data_distribution_type, dir, thread):
        # Step 1: Generate the workload configuration
        parent_dir = os.path.dirname(os.path.abspath(__file__))
        gp_dir = os.path.dirname(parent_dir)
        ycsb_dir = os.path.join(gp_dir, dir, 'YCSB-cpp')
        os.chdir(ycsb_dir)
        config_file = self.generate_workload_config(operation_size, operation_type, data_distribution_type)
        
        print(config_file)
        # Step 2: Load the data into RocksDB
        load_command = f"./ycsb -load -db rocksdb -s -P {config_file} -P rocksdb/rocksdb.properties -s"
        logging.info(f"Loading data with command: {load_command}")

        try:
            load_result = subprocess.run(load_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logging.info(load_result.stdout.decode())
        except subprocess.CalledProcessError as e:
            logging.error(f"Error occurred while loading data: {e.stderr.decode()}")
            return False

        # Step 3: Run the benchmark test
        run_command = f"./ycsb -run -db rocksdb -s -P {config_file} -P rocksdb/rocksdb.properties -s -threads {thread}"
        logging.info(f"Running benchmark with command: {run_command}")
        
        try:
            run_result = subprocess.run(run_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logging.info(run_result.stdout.decode())
        except subprocess.CalledProcessError as e:
            logging.error(f"Error occurred while running benchmark: {e.stderr.decode()}")

        # Step 4: Write benchmark results to the output file, including thread info
        result_file = self.get_unique_filename(self.output_dir, 'output.txt')
        with open(result_file, 'w') as f:
            f.write(f"Configuration File: {config_file}\n\n")
            f.write(f"Thread Count: {thread}\n\n")  # Write the thread count
            with open(config_file, 'r') as config_f:
                f.write("Configuration Content:\n")
                f.write(config_f.read() + "\n\n")
            f.write(run_result.stdout.decode())
            logging.info(f"Benchmark results saved to {result_file}")

        print("Benchmark completed successfully!")
