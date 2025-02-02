#!/usr/bin/env python3
import subprocess
import logging

def run_command(command, check=True):
    """Run a shell command."""
    logging.info(f"Running command: {' '.join(command)}")
    subprocess.run(command, check=check)

def install_packages():
    """Install packages globally using apt and pip."""
    # Update package list
    run_command(['sudo', 'apt', 'update'])

    # Install Python packages globally using pip
    run_command(['sudo', 'pip3', 'install', 'pandas', 'matplotlib', 'numpy', 'duckdb'])

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    install_packages()
    logging.info("Global setup complete.")
    