import os
import shutil
import subprocess
import logging
import sys

def run_command(command, check=True, shell=False):
    """Run a shell command."""
    logging.info(f"Running command: {' '.join(command)}")
    try:
        result = subprocess.run(command, check=check, shell=shell, text=True, capture_output=True)
        logging.info(result.stdout)
        if result.stderr:
            logging.warning(result.stderr)
        return result
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed with error: {e}")
        logging.error(e.stdout)
        logging.error(e.stderr)
    except FileNotFoundError as e:
        logging.error(f"Command not found: {e}")

def remove_directory(path):
    """Remove the specified directory if it exists."""
    if os.path.exists(path):
        try:
            shutil.rmtree(path)
            logging.info(f"Removed directory: {path}")
        except Exception as e:
            logging.error(f"Failed to remove directory {path}: {e}")

def find_pip_command():
    """Find the appropriate pip command."""
    for cmd in ['pip3', 'pip', 'python3 -m pip', 'python -m pip']:
        try:
            result = subprocess.run(f"{cmd} --version", shell=True, check=True, capture_output=True, text=True)
            logging.info(f"Found pip: {cmd} ({result.stdout.strip()})")
            return cmd
        except:
            pass
    return None

def uninstall_python_packages():
    """Uninstall Python packages used in the benchmark."""
    packages = ['numpy', 'pandas', 'matplotlib']
    pip_command = find_pip_command()
    if pip_command:
        for package in packages:
            run_command(f"{pip_command} uninstall -y {package}", shell=True)
            logging.info(f"Attempted to uninstall Python package: {package}")
    else:
        logging.error("No pip command found. Unable to uninstall Python packages.")

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logging.info(f"Script directory: {script_dir}")

    output_path = os.path.join(script_dir, 'output')
    remove_directory(output_path)

    # Check if sysbench is installed before trying to remove it
    if run_command(['which', 'sysbench'], check=False).returncode == 0:
        run_command(['sudo', 'apt', 'remove', '-y', 'sysbench'])
        run_command(['sudo', 'apt', 'purge', '-y', 'sysbench'])
    else:
        logging.info("sysbench is not installed, skipping removal.")

    uninstall_python_packages()

    run_command(['sudo', 'apt', 'autoremove', '-y'])
    run_command(['sudo', 'apt', 'clean'])

    logging.info("Cleanup complete. Attempted to remove all installed packages and output.")

if __name__ == "__main__":
    main()