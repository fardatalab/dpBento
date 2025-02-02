import os
import re
import csv
import argparse
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_info_from_filename(filename):
    """Extract parameter information from the filename."""
    try:
        # Remove 'openssl_speed_' prefix and timestamp suffix
        params_str = '_'.join(filename.split('_')[2:-1])
        param_dict = {}
        params = params_str.split('_')
        for param in params:
            parts = param.split('-')
            key = parts[0]
            value = '-'.join(parts[1:])  # Join back parts with '-' if there were multiple
            param_dict[key] = value
        return param_dict
    except Exception as e:
        logger.error(f"Error parsing filename {filename}: {str(e)}")
        return {}

def extract_throughput(content, algorithm):
    """Extract throughput information from file content."""
    pattern = rf"{re.escape(algorithm)}\s+([\d.]+)k"
    match = re.search(pattern, content)
    if match:
        return match.group(1)
    return "N/A"

def process_files(directory, metrics):
    """Process all result files in the directory."""
    results = []
    for filename in os.listdir(directory):
        if filename.startswith("openssl_speed_") and filename.endswith(".txt"):
            filepath = os.path.join(directory, filename)
            try:
                with open(filepath, 'r') as file:
                    content = file.read()
                
                info = extract_info_from_filename(filename)
                if not info:
                    logger.warning(f"Skipping file {filename} due to parsing error")
                    continue
                
                # Extract benchmark items and other parameters
                benchmark_items_match = re.search(r"Benchmark items: (.+)", content)
                benchmark_items = benchmark_items_match.group(1) if benchmark_items_match else "N/A"
                
                result = {
                    'Algorithm': info.get('alg', 'N/A'),
                    'Test Duration': f"{info.get('sec', 'N/A')} seconds",
                    'Data Block Size': f"{info.get('bytes', 'N/A')} bytes",
                    'Parallel Operations': info.get('multi', 'N/A'),
                    'Async Jobs': info.get('async', 'N/A'),
                    'Misalignment': f"{info.get('misalign', 'N/A')} bytes",
                    'Benchmark Items': benchmark_items,
                }
                
                # Only extract and include throughput if it's in the metrics list
                if "throughput" in metrics:
                    throughput = extract_throughput(content, info.get('alg', ''))
                    result['Throughput'] = f"{throughput}k"
                
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing file {filename}: {str(e)}")
    
    return results

def write_csv(results, output_file):
    """Write results to a CSV file."""
    if not results:
        logger.warning("No results to write to CSV.")
        return

    fieldnames = results[0].keys()
    
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    
    logger.info(f"Results written to {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Generate report from OpenSSL speed test results')
    parser.add_argument('--metrics', type=json.loads, default=[], help='JSON string of metrics')
    args = parser.parse_args()

    logger.info(f"Received metrics: {args.metrics}")

    # Directory containing the result files
    result_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),'output',)
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..', 'output', 'hashing')
    os.makedirs(output_dir, exist_ok=True)
    
    # Process files and get results
    results = process_files(result_dir, args.metrics)
    
    # Write results to CSV
    output_file = os.path.join(output_dir, 'openssl_results.csv')
    write_csv(results, output_file)

if __name__ == "__main__":
    main()