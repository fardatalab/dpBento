# remove the csv files

import os
from run import VALID_BENCHMARK_ITEMS


curr_dir = os.path.dirname(os.path.realpath(__file__))
for item in VALID_BENCHMARK_ITEMS:
    for f in os.listdir(os.path.join(curr_dir, item)):
        if f == 'result.csv':
            to_remove = os.path.join(curr_dir, item, f)
            print(f"Removing {to_remove}")
            os.remove(to_remove)

# remove if exist
if os.path.exists(os.path.join(curr_dir, 'output.csv')):
    os.remove(os.path.join(curr_dir, 'output.csv'))
print("Removed all csv files for compute benchmarks")