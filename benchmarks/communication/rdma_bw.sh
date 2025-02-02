#!/bin/bash

# Variables
HOST_USER="$1"
HOST_IP="$2"
PORT="$3"
OUTPUT_FILE="$4"
PASSWORD="$5"
HOST_IB_DEV="$6"
DPU_IB_DEV="$7"
DATA_SIZE="$8"
TEST_ROUND="$9"

# Function to SSH into the host and start ib_read_bw server, then exit
ssh_into_host() {
    echo "Starting SSH into $HOST_USER@$HOST_IP..."
    sshpass -p "$PASSWORD" ssh $HOST_USER@$HOST_IP "bash -s" <<EOF &
    echo "Connected to host $HOST_USER@$HOST_IP..."
    echo "Starting ib_read_bw server..."

    # Run the ib_read_bw server
    ib_read_bw -d "$HOST_IB_DEV"

    echo "ib_read_bw server started on $HOST_USER@$HOST_IP with device $HOST_IB_DEV"
    exit
EOF
    echo "SSH session to host $HOST_USER@$HOST_IP completed."
}

# Start SSH into the host to run the ib_read_bw server
echo "Starting ib_read_bw server on host..."
ssh_into_host

# Give the server some time to start
echo "Waiting for the server to start..."
sleep 10

# After the server is ready, run the client on the DPU
echo "Starting ib_read_bw client on the DPU..."

# Run ib_read_bw client and save output to file
ib_read_bw $HOST_IP -d $DPU_IB_DEV -n $TEST_ROUND -s $DATA_SIZE| tee $OUTPUT_FILE

echo "Client run completed. Statistics saved to $OUTPUT_FILE"
