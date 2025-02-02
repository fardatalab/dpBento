import argparse
import json
import os
import re
import csv
import logging
import numpy as np

iops_pattern = re.compile(r'IOPS=([\d.]+[kM]?)')
bw_pattern = re.compile(r'BW=([\d.]+[kM]?[KM]?iB/s)')

# Updated pattern to correctly extract clat average and its unit
clat_avg_pattern = re.compile(r'clat \((\w+)\):.*?avg=([\d.]+)', re.MULTILINE)
clat_percentile_pattern = re.compile(r'clat percentiles.*?\((\w+)\):', re.MULTILINE)
percentile_value_pattern = re.compile(r'\|\s*([\d.]+)\.00th=\[\s*(\d+)\]')

def parse_arguments():
    parser = argparse.ArgumentParser(description='Generate report from benchmark test results.')
    parser.add_argument('--metrics', type=str, required=True, help='JSON string of metrics to report')
    return parser.parse_args()

def convert_value(value):
    if isinstance(value, str):
        if value.endswith('k'):
            return float(value[:-1]) * 1e3
        elif value.endswith('M'):
            return float(value[:-1]) * 1e6
        elif value.endswith('KiB/s'):
            return float(value[:-5]) / 1024  # Convert KiB/s to MiB/s
        elif value.endswith('MiB/s'):
            return float(value[:-5])
        elif value.endswith('KB/s'):
            return float(value[:-4]) / 1024  # Convert KB/s to MiB/s
        elif value.endswith('MB/s'):
            return float(value[:-4])
    return float(value)

def convert_to_msec(value, unit):
    """Convert latency values to milliseconds."""
    value = float(value)
    if unit == 'nsec':
        return value / 1e6
    elif unit == 'usec':
        return value / 1e3
    elif unit == 'msec':
        return value
    else:
        logging.warning(f"Unknown unit: {unit}, treating as msec")
        return value

def extract_value(pattern, text):
    match = pattern.search(text)
    if match:
        return match.group(1)
    return None

def extract_clat_percentiles(text, unit):
    """Extract clatency percentiles and convert to msec."""
    matches = percentile_value_pattern.findall(text)
    return {float(match[0]): convert_to_msec(float(match[1]), unit) for match in matches}

def parse_benchmark_output(filepath):
    with open(filepath, 'r') as file:
        content = file.read()

    runs = content.split("\nRun #")
    results = []
    clat_percentile_results = []

    for run in runs[1:]:  # Skip the first split part before 'Run1'
        result = {}

        # Extract clatency average and its unit, and convert to msec immediately
        clat_avg_match = clat_avg_pattern.search(run)
        if clat_avg_match:
            unit = clat_avg_match.group(1)
            avg_clatency = float(clat_avg_match.group(2))
            avg_clatency = convert_to_msec(avg_clatency, unit)  # Convert to msec immediately
            result['avg_clatency'] = avg_clatency
        else:
            logging.warning(f"Could not find clatency average in the run")
            continue

        # Extract clatency percentiles unit
        clat_unit_match = clat_percentile_pattern.search(run)
        if clat_unit_match:
            clat_unit = clat_unit_match.group(1)
            # Extract clatency percentiles and convert to msec immediately
            clat_percentiles = extract_clat_percentiles(run, clat_unit)
            if clat_percentiles:
                clat_percentile_results.append(clat_percentiles)
        else:
            logging.warning(f"Could not find clatency percentiles in the run")

        iops = extract_value(iops_pattern, run)
        bw = extract_value(bw_pattern, run)
        
        result['IOPS'] = convert_value(iops) if iops else 0
        result['bandwidth'] = convert_value(bw) if bw else 0
        
        results.append(result)

    # Calculate the average for each percentile (already in msec)
    if clat_percentile_results:
        percentiles = clat_percentile_results[0].keys()
        avg_clat_percentiles = {percentile: np.mean([run[percentile] for run in clat_percentile_results])
                                for percentile in percentiles}
    else:
        avg_clat_percentiles = {}

    return results, avg_clat_percentiles

def process_files(output_folder, metrics):
    results = []
    percentiles_to_calculate = [int(re.findall(r'\d+', metric)[0]) for metric in metrics if "percentile" in metric]

    for test_type in ['randread', 'randwrite', 'read', 'write']:
        test_type_dir = os.path.join(output_folder, test_type)
        if not os.path.isdir(test_type_dir):
            continue

        for dir_name in os.listdir(test_type_dir):
            dir_path = os.path.join(test_type_dir, dir_name)
            if not os.path.isdir(dir_path):
                continue

            filepath = os.path.join(dir_path, "combined_results.txt")
            if not os.path.exists(filepath):
                logging.warning(f"combined_results.txt not found in {dir_path}")
                continue

            logging.info(f"Processing file: {filepath}")
            
            parsed_outputs, avg_clat_percentiles = parse_benchmark_output(filepath)
            
            if not parsed_outputs:
                logging.warning(f"No data extracted from {filepath}")
                continue

            iops_list = [output.get('IOPS', 0) for output in parsed_outputs]
            bw_list = [output.get('bandwidth', 0) for output in parsed_outputs]
            clatency_list = [output.get('avg_clatency', 0) for output in parsed_outputs]

            avg_iops = sum(iops_list) / len(iops_list) if iops_list else 0
            avg_bw = sum(bw_list) / len(bw_list) if bw_list else 0
            avg_clatency = sum(clatency_list) / len(clatency_list) if clatency_list else 0

            # Parse directory name for parameters
            params_match = re.match(r'(\w+)_(\d+)_(\w+)_(\w+)_(\d+)_(\d+)_(.+)', dir_name)
            
            if not params_match:
                logging.error(f"Unexpected directory name format: {dir_name}")
                continue

            block_size, numProc, size, runtime, direct, iodepth, io_engine = params_match.groups()

            result = {
                'test_lst': 'storage',
                'test_type': test_type,
                'block_sizes': block_size,
                'numProc': numProc,
                'size': size,
                'runtime': runtime,
                'direct': direct,
                'iodepth': iodepth,
                'io_engine': io_engine,
                'avg_clatency': avg_clatency,  # Already in msec
            }

            if "bandwidth" in metrics:
                result['bandwidth'] = avg_bw
            if "IOPS" in metrics:
                result['IOPS'] = avg_iops

            # Process percentile values
            if avg_clat_percentiles and percentiles_to_calculate:
                for percentile in percentiles_to_calculate:
                    if percentile in avg_clat_percentiles:
                        result[f'{percentile}th_percentile_clatency'] = avg_clat_percentiles[percentile]
                    else:
                        logging.warning(f"Percentile {percentile} not found in the data")

            results.append(result)
            logging.info(f"Processed test: {test_type}, block size: {block_size}, io_engine: {io_engine}")

    return results

def save_to_csv(results, output_folder, metrics):
    base_fields = ['test_lst', 'test_type', 'block_sizes', 'numProc', 'size', 'runtime', 'direct', 'iodepth', 'io_engine']
    
    metric_fields_map = {
        'avg_clatency': 'avg_clatency',
        'bandwidth': 'bandwidth',
        'IOPS': 'IOPS',
    }
    
    required_fields = base_fields[:]
    for metric in metrics:
        if "percentile" in metric:
            percentile = re.findall(r'\d+', metric)[0]
            required_fields.append(f'{percentile}th_percentile_clatency')
        elif metric in metric_fields_map:
            required_fields.append(metric_fields_map[metric])
    
    output_file = os.path.join(output_folder, 'results.csv')
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=required_fields)
        writer.writeheader()
        for result in results:
            # Convert all np.float64 types to standard Python float
            for key, value in result.items():
                if isinstance(value, np.float64):
                    result[key] = float(value)  # Convert to standard float type

            # Ensure all latency values are properly in msec
            if 'avg_clatency' in result:
                result['avg_clatency'] = float(result['avg_clatency'])
            for percentile in [key for key in result if 'percentile_clatency' in key]:
                result[percentile] = float(result[percentile])

            row = {field: result.get(field, '') for field in required_fields}
            writer.writerow(row)
    
    logging.info(f"Results saved to {output_file}")

def main():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    try:
        args = parse_arguments()
        metrics = json.loads(args.metrics)
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing metrics: {e}")
        return
    except Exception as e:
        logging.error(f"Error parsing arguments: {e}")
        return

    output_folder = os.path.join(os.path.dirname(__file__), 'output')
    logging.info(f"Output folder: {output_folder}")

    try:
        results = process_files(output_folder, metrics)
    except Exception as e:
        logging.error(f"Error processing files: {e}", exc_info=True)
        return

    try:
        save_to_csv(results, output_folder, metrics)
    except Exception as e:
        logging.error(f"Error saving to CSV: {e}", exc_info=True)

    print("Storage report.py successfully completed.")

if __name__ == '__main__':
    main()
