import os
import subprocess
import sys


this_dir = os.path.dirname(os.path.realpath(__file__))
doca_dir = os.path.join(this_dir, 'doca_compress')
build_dir = os.path.join(this_dir, 'build')
root_dir = os.path.join(this_dir, '..', '..')

def install_dependencies():
    subprocess.run(['pip3', 'install', 'zlib-ng'], check=True)

def compile_doca_compress():
    os.makedirs(build_dir, exist_ok=True)
    output = subprocess.run(['meson', build_dir], cwd=doca_dir, capture_output=True)
    # print(output.stdout)
    # print(output.stderr)
    output = subprocess.run(['ninja', '-C', build_dir], cwd=doca_dir, capture_output=True).stdout
    # print(output)

if __name__ == '__main__':
    install_dependencies()
    compile_doca_compress()
    print(f"Installed deps for compression benchmarks")