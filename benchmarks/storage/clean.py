import os
import shutil
import subprocess
import logging

def run_command(command, check=True, shell=False):
    """Run a shell command."""
    logging.info(f"Running command: {' '.join(command)}")
    subprocess.run(command, check=check, shell=shell)

def remove_directory(path):
    """Remove the specified directory if it exists, handling permission errors."""
    if os.path.exists(path):
        # Try changing permissions to ensure we can delete it
        for root, dirs, files in os.walk(path):
            for name in dirs:
                try:
                    os.chmod(os.path.join(root, name), 0o777)
                except Exception as e:
                    logging.warning(f"Failed to change permission for directory {name}: {e}")
            for name in files:
                try:
                    os.chmod(os.path.join(root, name), 0o777)
                except Exception as e:
                    logging.warning(f"Failed to change permission for file {name}: {e}")
        
        try:
            # Attempt to remove the directory
            shutil.rmtree(path)
            logging.info(f"Removed directory: {path}")
        except Exception as e:
            logging.error(f"Failed to remove directory {path}: {e}")

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

def clean_tmp_directory():
    """Clean up the /tmp directory."""
    tmp_path = '/tmp'
    logging.info(f"Cleaning up {tmp_path} directory...")
    remove_directory(tmp_path)
    # Recreate /tmp directory to avoid system issues
    os.makedirs(tmp_path, mode=0o1777, exist_ok=True)
    logging.info(f"Recreated {tmp_path} directory.")

def main():
    logging.basicConfig(level=logging.INFO)
    
    # Get the directory of the clean.py script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logging.info(f"Script directory: {script_dir}")

    # Remove the output directory within the script directory
    output_path = os.path.join(script_dir, 'output')
    remove_directory(output_path)

    # Uninstall packages
    remove_package('fio')
    remove_package('python3-pip')

    # Purge packages
    purge_package('fio')
    purge_package('python3-pip')

    # Remove any unused dependencies
    autoremove_unused_dependencies()

    # Clean up package cache
    clean_package_cache()


    logging.info("Cleanup complete. All installed packages and temporary files have been removed.")

if __name__ == "__main__":
    main()
