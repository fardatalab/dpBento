import subprocess
import sys

def run_command(command):
    try:
        subprocess.run(command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {command}")
        print(f"Error details: {e}")
        sys.exit(1)

def install_sysbench():
    print("Installing sysbench...")
    run_command("sudo apt-get update")
    run_command("sudo apt-get install -y sysbench")

def install_python_packages():
    print("Installing required Python packages...")
    required_packages = [
        'numpy',
        'pandas',
        'matplotlib'
    ]
    run_command(f"sudo apt-get install -y python3-pip")
    for package in required_packages:
        run_command(f"pip3 install {package}")

def main():
    print("Starting preparation for memory benchmark...")
    
    # Install sysbench
    install_sysbench()
    
    # Install Python packages
    install_python_packages()
    
    print("Preparation completed successfully.")

if __name__ == "__main__":
    main()