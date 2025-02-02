import os
import re
import csv
import argparse
import json
from datetime import datetime

def parse_arguments():
    parser = argparse.ArgumentParser(description='Generate report for memory benchmark')
    parser.add_argument('--metrics', type=str, help='JSON string of metrics to include in the report')
    return parser.parse_args()

def parse_filename(filename):
    pattern = r'result_(\d+[kKMG])_(\d+[KMGT])_(\w+)_(\w+)_(\d+)\.txt'
    match = re.match(pattern, filename)
    if match:
        return {
            'memory-block-size': match.group(1),
            'memory-total-size': match.group(2),
            'memory-oper': match.group(3),
            'memory-access-mode': match.group(4),
            'threads': match.group(5),
            'time': '10'  # Hardcoded as per the file names
        }
    return None

def parse_file_content(file_path, metrics):
    with open(file_path, 'r') as file:
        content = file.read()
    
    results = {}

    if 'bandwidth' in metrics:
        bandwidth_match = re.search(r'(\d+\.\d+) MiB transferred \(([\d.]+) MiB/sec\)', content)
        if bandwidth_match:
            results['bandwidth'] = bandwidth_match.group(2)

    if 'latency' in metrics:
        events_match = re.search(r'total number of events:\s+(\d+)', content)
        latency_sum_match = re.search(r'sum:\s+([\d.]+)', content)
        
        if events_match and latency_sum_match:
            total_events = int(events_match.group(1))
            latency_sum_ms = float(latency_sum_match.group(1))
            avg_latency_ns = (latency_sum_ms * 1e6) / total_events
            results['latency'] = f"{avg_latency_ns:.2f}"

    return results

def main():
    args = parse_arguments()
    metrics = json.loads(args.metrics)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(current_dir, 'output')

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f'benchmark_results_{timestamp}.csv'
    csv_path = os.path.join(output_dir, csv_filename)
    
    headers = ['memory-block-size', 'memory-total-size', 'memory-oper', 'memory-access-mode', 'threads', 'time'] + metrics
    
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        
        for filename in sorted(os.listdir(output_dir)):
            if filename.startswith('result_') and filename.endswith('.txt'):
                file_path = os.path.join(output_dir, filename)
                params = parse_filename(filename)
                
                if params:
                    results = parse_file_content(file_path, metrics)
                    params.update(results)
                    writer.writerow(params)
    
    print(f"CSV report generated: {csv_path}")

if __name__ == "__main__":
    main()