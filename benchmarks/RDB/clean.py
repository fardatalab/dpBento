#!/usr/bin/env python3
import subprocess
import argparse
import logging
import sys
import os
import shutil

def uninstall_packages(packages):
    """Uninstall packages using pip."""
    pip_executable = 'pip3'
    for package in packages:
        try:
            subprocess.run(['sudo',pip_executable, 'uninstall', '-y', package])
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to uninstall {package}: {e}")

def delete_output_directory(output_dir):
    # Check if the output directory exists and delete it
    if os.path.exists(output_dir):
        try:
            shutil.rmtree(output_dir)
            print(f"Output directory '{output_dir}' and all its contents have been deleted.")
        except Exception as e:
            print(f"Error occurred while deleting the output directory: {e}")
            sys.exit(1)
    else:
        print(f"The output directory '{output_dir}' does not exist.")

def main():
    # Setup logging
    logging.basicConfig(level=logging.INFO)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, 'output')

    # Define the packages to uninstall
    packages_to_uninstall = ['pandas', 'matplotlib', 'numpy', 'duckdb']

    delete_output_directory(output_dir)

    # Uninstall the packages
    uninstall_packages(packages_to_uninstall)

if __name__ == '__main__':
    main()