
#!/bin/bash
# Variables
HOST_USER="$1"
HOST_IP="$2"
PORT="$3"
FILE_SIZE="$4"
THREADS="$5"
TOTAL_REQUESTS="$6"
LOCAL_DIRECTORY="$7" # Replace with the path to the local directory
OUTPUT_FILE="$8"
PASSWORD="$9"
isBW="${10}"
REMOTE_DIRECTORY="/tmp" # The directory on the remote host

# Function to SSH into farnet1 and run a script, then exit
ssh_into_host() {
    echo "Starting SSH into $HOST_USER@$HOST_IP..."
    sshpass -p "$PASSWORD" ssh $HOST_USER@$HOST_IP "bash -s" << EOF
    echo "Connected to host $HOST_USER@$HOST_IP..."
    cd $REMOTE_DIRECTORY && cd benchmark_tcp
    echo "Running server.sh..."
    ./server.sh $PORT $TOTAL_REQUESTS $THREADS
    exit
EOF
    echo "SSH session to host $HOST_USER@$HOST_IP completed."
}

# SCP the directory to host
scp -r $LOCAL_DIRECTORY $HOST_USER@$HOST_IP:$REMOTE_DIRECTORY

sleep 5

echo "Now ssh into the host"

# Run SSH into farnet1 in the background
ssh_into_host &

# Give the server some time to start
echo "Waiting for the server to start..."
sleep 5

# After the background process (SSH to farnet1) completes, continue on the DPU

echo "Starting the client on the DPU..."
cd $LOCAL_DIRECTORY
cd client || { echo "Directory client not found"; exit 1; }
gcc -o client client.c -lpthread|| { echo "Compilation failed"; exit 1; }
./client $HOST_IP $PORT $FILE_SIZE $THREADS 1 $TOTAL_REQUESTS $OUTPUT_FILE $isBW
# HOST_IP, PORT, FILE_SIZE, THREADS, TARGET_METRIC (1 defaults to everything), TOTAL_REQUESTS

echo "Client run completed."
