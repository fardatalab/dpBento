import os
import shutil
import subprocess
import logging

def run_command(command, check=True, shell=False):
    """Run a shell command."""
    logging.info(f"Running command: {' '.join(command)}")
    subprocess.run(command, check=check, shell=shell)

def remove_directory(path):
    """Remove the specified directory if it exists."""
    if os.path.exists(path):
        shutil.rmtree(path)
        logging.info(f"Removed directory: {path}")

def remove_package(package_name):
    """Remove the specified package using apt."""
    run_command(['sudo', 'apt', 'remove', '-y', package_name])
    logging.info(f"Uninstalled package: {package_name}")

def purge_package(package_name):
    """Purge the specified package using apt."""
    run_command(['sudo', 'apt', 'purge', '-y', package_name])
    logging.info(f"Purged package: {package_name}")

def autoremove_unused_dependencies():
    """Remove any unused dependencies."""
    run_command(['sudo', 'apt', 'autoremove', '-y'])
    logging.info("Removed unused dependencies.")

def clean_package_cache():
    """Clean up package cache."""
    run_command(['sudo', 'apt', 'clean'])
    logging.info("Cleaned up package cache.")

def main():
    logging.basicConfig(level=logging.INFO)
    
    # Get the directory of the clean.py script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logging.info(f"Script directory: {script_dir}")

    # Remove the output directory within the script directory
    output_path = os.path.join(script_dir, 'output')
    remove_directory(output_path)

    # Uninstall packages
    remove_package('python3-pip')

    # Purge packages
    purge_package('python3-pip')

    # Remove any unused dependencies
    autoremove_unused_dependencies()

    # Clean up package cache
    clean_package_cache()
    
    logging.info("Cleanup complete. All installed packages have been removed.")

if __name__ == "__main__":
    main()
