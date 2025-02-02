import argparse
import os
import csv

def parse_arguments():
    parser = argparse.ArgumentParser(description='Communication benchmark')
    parser.add_argument('--metrics', type=str, default='', help='Metrics to collect in the generated file')
    args = parser.parse_args()
    return args

def parse_rdma_latency(metrics):
    
    output_file = os.path.join(os.path.dirname(__file__), 'output', 'RDMA', f'latency_output.txt')
    
    if not os.path.exists(output_file):
        print(f"No such file or directory: '{output_file}'")
        return

    with open(output_file, 'r') as f:
        contents = f.read()

    # Split the content into sections separated by the separator line
    sections = contents.split('---------------------------------------------------------------------------------------')

    # Find the section that contains the table
    table_section = None
    for section in sections:
        if '#bytes' in section:
            table_section = section
            break

    if table_section is None:
        print('Table section not found in output.')
        return

    # Clean and split the table section into lines
    lines = [line.strip() for line in table_section.strip().split('\n') if line.strip()]

    if len(lines) < 2:
        print('Not enough lines in table section.')
        return

    header_line = lines[0]
    data_line = lines[1]

    # Correctly handling '99%' and '99.9%' percentile headers
    header_line = header_line.replace('99% percentile[usec]', '99_percentile[usec]').replace('99.9% percentile[usec]', '99.9_percentile[usec]')
    header_fields = header_line.split()
    data_values = data_line.split()

    if len(header_fields) != len(data_values):
        print('Number of data values does not match number of header fields.')
        return

    # Write the headers and data into a CSV file
    output_csv = os.path.join(os.path.dirname(__file__), 'output', 'RDMA', 'latency_output.csv')
    file_exists = os.path.exists(output_csv)
    
    with open(output_csv, 'a', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)

        # If the file doesn't exist or is empty, write the headers
        if not file_exists:
            csvwriter.writerow(header_fields)
        # else:
        #     # Read the first row to check if headers already exist
        #     with open(output_csv, 'r') as readfile:
        #         existing_headers = csv.reader(readfile)
        #         first_row = next(existing_headers, None)
        #         if first_row != header_fields:
        #             csvwriter.writerow(header_fields)  # Append headers if different

        # Append data values
        csvwriter.writerow(data_values)
        
        

def parse_rdma_bw(metrics):
    if "bandwidth" in metrics:
        output_file = os.path.join(os.path.dirname(__file__), 'output', 'RDMA', f'bandwidth_output.txt')

        if not os.path.exists(output_file):
            print(f"No such file or directory: '{output_file}'")
            return

        with open(output_file, 'r') as f:
            contents = f.read()
            
        # Extract BW peak and BW average
        lines = contents.splitlines()
        bw_data = []

        found_bw_peak = False
        for line in lines:
            if "BW peak" in line or "MsgRate" in line:
                found_bw_peak = True
                continue
            
            if found_bw_peak:  # The next line after "BW peak" is what we want
                parts = line.strip().split()
                bw_peak = float(parts[2])   # Extract BW peak value
                bw_avg = float(parts[3])    # Extract BW average value
                bw_data.append((bw_peak, bw_avg))
                
                found_bw_peak = False  # Reset after processing the next line

        output_csv = os.path.join(os.path.dirname(__file__), 'output', 'RDMA', 'latency_output.csv')
        headers = ["BW Peak (MB/sec)","BW Average (MB/sec)"]
        values = [bw_peak, bw_avg]

        
        with open(output_csv, 'r') as csvfile:
            csvreader = list(csv.reader(csvfile))
            
            # Check if the new headers already exist in the first row
            if all(header in csvreader[0] for header in headers):
                print("Headers already exist.")
            else:
                # Append new headers if they don't exist
                csvreader[0].extend(headers)

            # Check if the new values already exist in the second row
            if all(value in csvreader[-1] for value in headers):
                print("Values already exist.")
            else:
                # Append new values if they don't exist
                csvreader[-1].extend(values)
        
        with open(output_csv, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerows(csvreader)

        print(f'Bandwidth data successfully written to {output_csv}')

if __name__ == '__main__':
    args = parse_arguments()
    parse_rdma_latency(args.metrics)
    parse_rdma_bw(args.metrics)
