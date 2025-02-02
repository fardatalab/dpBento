import os
import subprocess
import sys

this_dir = os.path.dirname(os.path.realpath(__file__))
doca_dir = os.path.join(this_dir, 'doca_sha256')
build_dir = os.path.join(this_dir, 'build')
root_dir = os.path.join(this_dir, '..', '..')
# print(f"root: {root_dir}")


def update_openssl():
    try:
        print("Updating package list...")
        # subprocess.run(['sudo', 'apt', 'update'], check=True)
        
        # let's not upgrade for now
        # print("Upgrading OpenSSL...")
        # subprocess.run(['sudo', 'apt', 'upgrade', '-y', 'openssl'], check=True)
        
        # print("OpenSSL update completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error updating OpenSSL: {e}")
        return False

def compile_doca_hash():
    os.makedirs(build_dir, exist_ok=True)
    output = subprocess.run(['meson', build_dir], cwd=doca_dir, capture_output=True)
    # print(output.stdout)
    # print(output.stderr)
    output = subprocess.run(['ninja', '-C', build_dir], cwd=doca_dir, capture_output=True).stdout
    # print(output)

def main():
    if update_openssl():
        print("Preparation completed successfully.")
    else:
        print("Preparation failed.")
        sys.exit(1)
    compile_doca_hash()

if __name__ == "__main__":
    main()