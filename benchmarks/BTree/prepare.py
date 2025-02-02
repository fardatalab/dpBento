import subprocess
import os
import logging

def run_command(command, check=True, shell=False):
    """Run a shell command."""
    logging.info(f"Running command: {' '.join(command)}")
    try:
        subprocess.run(command, check=check, shell=shell)
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed with error: {e}")
        raise

def set_directory_executable(directory):
    """Recursively set all scripts in the directory to be executable."""
    if not os.path.isdir(directory):
        logging.warning(f"Directory not found: {directory}. Skipping.")
        return

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".sh") or file.endswith(".py"):  # Target only .sh and .py files
                file_path = os.path.join(root, file)
                logging.info(f"Setting executable permission for: {file_path}")
                try:
                    os.chmod(file_path, 0o755)  # Set file permission to be executable
                except Exception as e:
                    logging.error(f"Failed to set permission for {file_path}: {e}")

def main():
    logging.basicConfig(level=logging.INFO)

    # Get the directory of the prepare.py script
    benchmark_dir = os.path.dirname(os.path.abspath(__file__))
    logging.info(f"Benchmark directory: {benchmark_dir}")

    # Update and install necessary system packages
    run_command(['sudo', 'apt', 'update'])
    run_command(['sudo', 'apt', 'install', '-y', 'cmake', 'liblmdb0', 'liblmdb-dev', 'zlib1g-dev', 'unzip'])

    # Set execute permissions for all scripts in specified directories
    directories_to_set_executable = [
        os.path.join(benchmark_dir, "/YCSB-cpp"),
    ]
    for directory in directories_to_set_executable:
        set_directory_executable(directory)
    os.chdir(benchmark_dir + "/YCSB-cpp/")
    #print(os.getcwd())
    run_command(["make", "BIND_LMDB=1"])
    os.chdir("../")
    # Create and initialize a results.csv file
    results_file_path = os.path.join(benchmark_dir, "results.csv")
    os.makedirs(os.path.dirname(results_file_path), exist_ok=True)  # Ensure results directory exists
    with open(results_file_path, "w") as f:
        f.write("num_threads" + chr(9) + "num_records" + chr(9) + "num_operations" + chr(9) + "throughput(ops/sec)" + chr(9) + "\n")

    logging.info("Setup complete")

if __name__ == "__main__":
    main()
