import argparse
import os
import subprocess
import datetime

def parse_arguments():
    parser = argparse.ArgumentParser(description='Run memory benchmark')
    parser.add_argument('--benchmark_items', type=str, help='Comma-separated list of benchmark items')
    parser.add_argument('--memory-block-size', type=str, help='Memory block size')
    parser.add_argument('--memory-total-size', type=str, help='Total memory size')
    parser.add_argument('--memory-oper', type=str, help='Memory operation')
    parser.add_argument('--memory-access-mode', type=str, help='Memory access mode')
    parser.add_argument('--threads', type=int, help='Number of threads')
    parser.add_argument('--time', type=int, help='Test duration in seconds')
    parser.add_argument('--metrics', type=str, help='JSON string of metrics to measure')
    
    return parser.parse_args()

def run_sysbench(args):
    command = [
        'sysbench',
        'memory',
        f'--memory-block-size={args.memory_block_size}',
        f'--memory-total-size={args.memory_total_size}',
        f'--memory-oper={args.memory_oper}',
        f'--memory-access-mode={args.memory_access_mode}',
        f'--threads={args.threads}',
        f'--time={args.time}',
        'run'
    ]
    
    result = subprocess.run(command, capture_output=True, text=True)
    return result.stdout

def save_output(output, args):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(current_dir, 'output')
    
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"result_{args.memory_block_size}_{args.memory_total_size}_{args.memory_oper}_{args.memory_access_mode}_{args.threads}.txt"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w') as f:
        f.write(output)
    
    print(f"Sysbench output saved to {filepath}")

def main():
    args = parse_arguments()
    
    print(f"Running memory benchmark with parameters:")
    print(f"  Benchmark items: {args.benchmark_items}")
    print(f"  Memory block size: {args.memory_block_size}")
    print(f"  Memory total size: {args.memory_total_size}")
    print(f"  Memory operation: {args.memory_oper}")
    print(f"  Memory access mode: {args.memory_access_mode}")
    print(f"  Threads: {args.threads}")
    print(f"  Time: {args.time} seconds")
    print(f"  Metrics: {args.metrics}")
    
    output = run_sysbench(args)
    save_output(output, args)

if __name__ == '__main__':
    main()