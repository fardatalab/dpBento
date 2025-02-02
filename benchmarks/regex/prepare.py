import os
import subprocess
import sys


this_dir = os.path.dirname(os.path.realpath(__file__))
doca_dir = os.path.join(this_dir, 'doca_regex')
build_dir = os.path.join(this_dir, 'build')
root_dir = os.path.join(this_dir, '..', '..')

def compile_doca_regex():
    os.makedirs(build_dir, exist_ok=True)
    output = subprocess.run(['meson', build_dir], cwd=doca_dir, capture_output=True)
    # print(output.stdout)
    # print(output.stderr)
    output = subprocess.run(['ninja', '-C', build_dir], cwd=doca_dir, capture_output=True).stdout
    # print(output)

def install_dependencies():
    # subprocess.run(f"sudo apt install libvectorscan-dev", shell=True, check=True)
    # subprocess.run(f"sudo apt install libvectorscan5", shell=True, check=True)
    subprocess.run(f"sudo apt-get install libboost-all-dev build-essential cmake ragel pkg-config libsqlite3-dev libpcap-dev -y", shell=True, check=True)

def build_vectorscan():
    subprocess.run(f"sudo apt build-essential cmake ragel pkg-config libsqlite3-dev libpcap-dev", shell=True, check=True)
    subprocess.run(f"git clone https://github.com/VectorCamp/vectorscan.git", shell=True, check=True)
    os.makedirs(os.path.join(this_dir, 'vectorscan', 'build'), exist_ok=True)
    build_dir = os.path.join(this_dir, 'vectorscan', 'build')
    try:
        subprocess.run(f"cmake ../", cwd=build_dir, shell=True, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(e.stderr)
        print(e.stdout)

def compile_benchmark():
    subprocess.run("g++ -I/usr/local/include/hs/ -L/usr/local/lib/ -L/usr/local/lib/ hyperscan.cpp -lhs -o hs")
    subprocess.run("g++ -I/usr/local/include/hs/ -L/usr/local/lib/ -L/usr/local/lib/ hyperscan-simd.cpp -lhs -o hs-simd")


if __name__ == '__main__':
    compile_doca_regex()
    # install_dependencies()
    # build_vectorscan()
    # compile_benchmark()
    print(f"prepared regex benchmarks")