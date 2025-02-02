import json
import os
import subprocess
from itertools import product
import argparse
import logging
from typing import List

# These scripts need to be executable in the benchmark item directory
BENCH_ITEM_SCRIPTS = ['prepare.py', 'run.py', 'report.py', 'clean.py']

class ExperimentRunner:
    def __init__(self, config_file):
        # Set up logging
        self.logger = self.setup_logging()

        self.config = self.load_config(config_file)

        # Get the directory of the current script as the dpbento root directory
        self.dpbento_root = os.path.dirname(os.path.abspath(__file__))
        self.benchmarks_dir = os.path.join(self.dpbento_root, 'benchmarks')

        # Set the output directory
        self.output_dir = os.path.join(self.dpbento_root, 'output')

        self.bench_items = {}
        '''
        Dictionary mapping benchmark class's path to a list[str] of benchmark items from the user config.
        This is essentially a parameter that will be passed alongside `bench_params` to the benchmark run.py script.
        '''

        self.bench_params = {}
        '''Dictionary mapping benchmark class's path to parameters from the user config'''

        self.bench_metrics = {}
        '''Dictionary mapping benchmark class's path to metrics from the user config'''

        self.bench_hints = {}
        '''Dictionary mapping benchmark class's path to (report/plot) hints from the user config'''

        # Get the list of benchmark paths to run, and then find scripts in these paths
        self.benchmarks_to_run = []
        self.collect_all_benchmarks_to_run()
        '''List of benchmark item paths to run, including user-provided benchmarks'''

        self.logger.debug('Using output directory: %s, dpbento root directory: %s', self.output_dir, self.dpbento_root)

    @staticmethod
    def setup_logging():
        logger = logging.getLogger('dpbento')
        logger.setLevel(logging.DEBUG)

        # Create a console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        # Create a formatter and add it to the handler
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)

        # Add the handler to the logger
        logger.addHandler(ch)
        return logger
    
    def load_config(self, config_file) -> dict:
        with open(config_file, 'r') as f:
            config = json.load(f)
        return config

    def create_and_check_directories(self):
        try:
            os.makedirs(self.dpbento_root, exist_ok=True)
            if not os.access(self.dpbento_root, os.R_OK | os.W_OK | os.X_OK):
                raise PermissionError(f"Cannot access dpbento directory '{self.dpbento_root}'. Please check your permissions.")
        except PermissionError as e:
            print(f"PermissionError: Unable to create directory '{self.dpbento_root}'. Please check your permissions.")
            raise e

        try:
            os.makedirs(self.output_dir, exist_ok=True)
            if not os.access(self.output_dir, os.R_OK | os.W_OK | os.X_OK):
                raise PermissionError(f"Cannot access output directory '{self.output_dir}'. Please check your permissions.")
        except PermissionError as e:
            print(f"PermissionError: Unable to create directory '{self.output_dir}'. Please check your permissions.")
            raise e

        # Also check permissions for the benchmark directory
        if not os.access(self.benchmarks_dir, os.R_OK | os.W_OK | os.X_OK):
            raise PermissionError(f"Cannot access benchmark directory '{self.benchmarks_dir}'. Please check your permissions.")
        self.logger.info(f"Benchmark directory and permissions verified.")

    def run_benchmark_script(self, script_name: str, benchmark: str, opts: list=[]):
            script_path = os.path.join(benchmark, script_name)
            commands = ['python3', script_path] + opts
            try:
                subprocess.run(commands, check=True)
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Running {script_name.split('.')[0]} for {benchmark} failed, error: {e}")
                return False
            return True

    def collect_all_benchmarks_to_run(self):
        '''
        Check the user JSON config file and collect all benchmarks to run, including user-provided benchmarks.
        
        Add benchmark items (paths) to `self.benchmarks_to_run`,
        and add parameters from the user config to the `self.bench_params` dictionary.
        Metrics and hints are also added to the `self.bench_metrics` and `self.bench_hints` dictionaries, respectively.
        
        Returns: None
        '''
        # NOTE: right now it params, metrics and hints are shared across items in the same class, let's still
        # store them in the dictionaries with its own item path as the key
        def add_bench_item_if_ok(item_path: str, bench_items: list, bench_params: dict, metrics: list, hints: dict):
            '''
            Add benchmark items (paths) to the list of benchmarks to run,
            and add parameters from the user config to the `bench_params` dictionary where the key is the item path,
            if all scripts look okay (currently executable).
            '''
            if all(map(lambda script: os.access(os.path.join(item_path, script), os.R_OK), BENCH_ITEM_SCRIPTS)):
                self.logger.info(f"Registering benchmark '{item_path}'")
                self.bench_items[item_path] = bench_items
                self.benchmarks_to_run.append(item_path)
                self.bench_params[item_path] = bench_params
                self.bench_metrics[item_path] = metrics
                self.bench_hints[item_path] = hints
                self.logger.debug(f"bench_params: {bench_params}")
            else:
                self.logger.warning(f"Benchmark '{item_path}' missing executable scripts, ignoring...")

        benchmark: dict

        for benchmark in self.config['benchmarks']:
            bench_class = benchmark["benchmark_class"]
            
            bench_items = benchmark.get("benchmark_items", [])

            # parameters, metrics and hints are shared across all benchmark items in the same class
            bench_params = benchmark.get("parameters", {})
            metrics = benchmark.get("metrics", [])
            hints = benchmark.get("report_hints", {})

            bench_class_path = os.path.join(self.benchmarks_dir, bench_class)
            if not os.access(bench_class_path, os.X_OK):
                self.logger.warning(f"Cannot access benchmark class '{bench_class}', ignoring...")
                continue

            # if not specified, try to get all benchmark items in the class
            # TODO: may need a more robust method to get all benchmark items
            if not bench_items:
                # get all bench items dirs in the bench class
                # NOTE: this tries to ignore the python virtual env directory
                # NOTE: and assumes each bench item has its own directory
                bench_items = [item_dir for item_dir in os.listdir(bench_class_path)
                                if (os.path.isdir(os.path.join(bench_class_path, item_dir)) and not item_dir.endswith('env'))]


                add_bench_item_if_ok(bench_class_path, bench_items, bench_params, metrics, hints)
                # bench_items_paths = [item_path for item_dir in os.listdir(bench_class_path)
                #                     if os.path.isdir(item_path:=os.path.join(bench_class_path, item_dir))]
                # for bench_items_path in bench_items_paths:
                #     # get the benchmark scripts and check if executable
                #     add_bench_item_if_ok(bench_items_path, {}, [], {})
            else:
                add_bench_item_if_ok(bench_class_path, bench_items, bench_params, metrics, hints)
                for bench_item in bench_items:
                    bench_item_path = os.path.join(bench_class_path, bench_item)
                    if not os.access(bench_item_path, os.X_OK):
                        self.logger.info(f"Cannot access benchmark item dir '{bench_item}', ignoring...")

        self.logger.info(f"Collected benchmarks to run: {self.benchmarks_to_run}")

    def run_dpbento(self):
        '''
        This is the main function for the dpbento framework.
        '''

        self.create_and_check_directories()

        for benchmark in self.benchmarks_to_run:
            if not self.run_benchmark_script('prepare.py', benchmark):
                continue

            bench_params = self.bench_params[benchmark]
            keys = bench_params.keys()
            values = (v if isinstance(v, list) else [v] for v in bench_params.values())
            combinations = list(product(*values))


            metrics_opt = f"--metrics={json.dumps(self.bench_metrics[benchmark])}"

            for combination in combinations:
                params = list(zip(keys, combination))
                opts = self.kv_list_to_opts(self.bench_items[benchmark], params)

                opts.append(metrics_opt)
                
                self.logger.info(f"Running benchmark {benchmark} with: {' '.join(opts)}")
                if not self.run_benchmark_script('run.py', benchmark, opts=opts):
                    continue

            # Add metrics parameters and run report.py
            # TODO: maybe just use comma separated values instead of json
            metrics_opts = [f"--metrics={json.dumps(self.bench_metrics[benchmark])}"]
            if not self.run_benchmark_script('report.py', benchmark, opts=metrics_opts):
                continue

    @staticmethod
    def kv_list_to_opts(bench_item, kv_list):
        opts = ['--benchmark_items', ','.join(bench_item)]#str(bench_item).strip('[]')
        for key, value in kv_list:
            opts.append(f"--{key}")
            opts.append(str(value))
        return opts

    def clean_benchmarks(self):
        '''
        Run clean.py to remove intermediate files for each benchmark item and reset state.
        '''
        for benchmark in self.benchmarks_to_run:
            self.run_benchmark_script('clean.py', benchmark)

def main():
    parser = argparse.ArgumentParser(description='Welcome to DPU benchmarking.')
    parser.add_argument('--config', type=str, required=True, help='Path to the configuration file')
    parser.add_argument('--clean', action='store_true', help='Run clean scripts')
    # TODO: may or may not need a standalone plot option
    # parser.add_argument('--report_only', action='store_true', help='rerun reports for already obtained results')
    args = parser.parse_args()

    runner = ExperimentRunner(args.config)

    if args.clean:
        runner.clean_benchmarks()
    else:
        runner.run_dpbento()

if __name__ == '__main__':
    main()
