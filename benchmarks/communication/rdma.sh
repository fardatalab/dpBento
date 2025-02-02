#!/bin/bash

# Variables
HOST_USER="$1"
HOST_IP="$2"
PORT="$3"
FILE_SIZE="$4"
THREADS="$5"
TOTAL_REQUESTS="$6"
OUTPUT_FILE="$7"
PASSWORD="$8"
HOST_IB_DEV="$9"
DPU_IB_DEV="${10}"

# Function to SSH into farnet1 and run a script, then exit
ssh_into_host() {
    echo "Starting SSH into $HOST_USER@$HOST_IP..."
    sshpass -p "$PASSWORD" ssh $HOST_USER@$HOST_IP "bash -s" << EOF &
    echo "Connected to host $HOST_USER@$HOST_IP..."
    echo "Running server $METRIC metric..."
    ib_read_lat -d "$HOST_IB_DEV"
    exit
EOF
    echo "SSH session to host $HOST_USER@$HOST_IP completed."
}

# SCP the directory to host
echo "Now ssh into the host"

# Run SSH into farnet1 in the background
ssh_into_host

# Give the server some time to start
echo "Waiting for the server to start..."
sleep 10

# After the background process (SSH to farnet1) completes, continue on the DPU
echo "Starting the client on the DPU..."
ib_read_lat $HOST_IP -d $DPU_IB_DEV -n $TOTAL_REQUESTS -s $FILE_SIZE| tee $OUTPUT_FILE

echo "Client run completed. Statistics saved to $OUTPUT_FILE"