import os
import shutil
import logging

def remove_directory(path):
    """Remove the specified directory if it exists."""
    if os.path.exists(path):
        shutil.rmtree(path)
        logging.info(f"Removed directory: {path}")

def remove_file(path):
    """Remove the specified file if it exists."""
    if os.path.exists(path):
        os.remove(path)
        logging.info(f"Removed file: {path}")

def main():
    logging.basicConfig(level=logging.INFO)
    
    # Get the directory of the clean.py script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logging.info(f"Script directory: {script_dir}")

    # Remove the output directory within the script directory
    output_path = os.path.join(script_dir, 'output')
    remove_directory(output_path)


    # Remove the CSV report file if it exists
    csv_report = os.path.join(script_dir, 'openssl_speed_test_results.csv')
    remove_file(csv_report)

    logging.info("Cleanup complete. All benchmark outputs and temporary files have been removed.")

if __name__ == "__main__":
    main()