import argparse
import os
import subprocess


def install_dependencies():
    # print('installing stress-ng...')
    # subprocess.run("sudo apt install stress-ng python3-venv -y", shell=True, check=True)
    subprocess.run("pip install pandas", shell=True, check=True)
    # subprocess.run("pip install numpy", shell=True, check=True)
    
    # get dir of current file
    # env_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'compute_env')
    # print(env_dir)
    # # create and use a virtual environment
    # print('creating virtual environment...')
    # subprocess.run(f"python3 -m venv {env_dir}", shell=True, check=True)
    # subprocess.run(f"source {env_dir}/bin/activate;\
    #                pip install pandas", shell=True, check=True, executable='/bin/bash')

def compile_exec():
    fp_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'float')
    int_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'int')
    print('compiling compute benchmarks...')
    subprocess.run(f"gcc -o int32 {int_path}/int32.c", shell=True, check=True)
    subprocess.run(f"gcc -o int8 {int_path}/int8.c", shell=True, check=True)
    subprocess.run(f"gcc -o int128 {int_path}/int128.c", shell=True, check=True)
    subprocess.run(f"gcc -o fp32 {fp_path}/fp32.c", shell=True, check=True)
    subprocess.run(f"gcc -o double {fp_path}/double.c", shell=True, check=True)
    print('compiled compute benchmarks')

if __name__ == '__main__':
    install_dependencies()
    compile_exec()
    print(f"Installed deps for compute benchmarks")