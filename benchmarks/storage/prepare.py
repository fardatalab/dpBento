import os
import subprocess
import logging

def run_command(command, check=True, shell=False):
    """Run a shell command."""
    logging.info(f"Running command: {' '.join(command)}")
    subprocess.run(command, check=check, shell=shell)

def install_packages(requirements_path):
    """Install packages globally using pip."""
    run_command(['pip3', 'install', '--upgrade', 'pip'])
    if os.path.exists(requirements_path):
        run_command(['pip3', 'install', '-r', requirements_path])
    else:
        logging.warning(f"requirements.txt not found at {requirements_path}")

def main():
    logging.basicConfig(level=logging.INFO)

    # Get the directory of the prepare.py script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logging.info(f"Script directory: {script_dir}")

    # Set the benchmark directory to the script directory
    benchmark_dir = script_dir

    # Update package list
    run_command(['sudo', 'apt', 'update'])

    # Install fio
    run_command(['sudo', 'apt', 'install', '-y', 'fio'])

    # Install python3-pip
    run_command(['sudo', 'apt', 'install', '-y', 'python3-pip'])

    # Install packages globally from requirements.txt
    requirements_path = os.path.join(benchmark_dir, 'requirements.txt')
    install_packages(requirements_path)

    logging.info("Setup complete. Python packages have been installed globally.")

if __name__ == "__main__":
    main()
