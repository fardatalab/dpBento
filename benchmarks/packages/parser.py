import argparse


class Parser:
    def __init__(self):
        self.parser = argparse.ArgumentParser(description='Run benchmarks.')
        self._add_arguments()

    def _add_arguments(self):
        self.parser.add_argument('--benchmark_items', type=str, help='Comma-separated list of benchmark items')
        # self.parser.add_argument('--output_dir', type=str, required=True, help='default output directory')

    def parse_arguments(self):
        return self.parser.parse_args()
