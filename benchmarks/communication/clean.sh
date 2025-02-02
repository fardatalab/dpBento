#!/bin/bash

# Variables
HOST_USER="$1"
HOST_IP="$2"
PASSWORD="$3"

# Function to SSH into host and run a script, then exit
ssh_into_host() {
    echo "Starting SSH into $HOST_USER@$HOST_IP..."
    sshpass -p "$PASSWORD" ssh $HOST_USER@$HOST_IP "bash -s" << 'EOF' &
    echo "Connected to host $HOST_USER@$HOST_IP..."
    rm -rf /tmp/benchmark_tcp
    echo "Removed /tmp/benchmark_tcp"
    exit
EOF
    echo "SSH session to host $HOST_USER@$HOST_IP completed."
}

echo "Now ssh into the host"

# Run SSH into host in the background
ssh_into_host