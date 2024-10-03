#!/bin/bash

# Username for SSH connection
username="digit"

# List of server IP addresses
servers=(172.20.96.20 172.20.96.16 172.20.96.22)

# Remote directory to pull
remote_dir="$HOME/scripts/"

# Loop through each server
for server in "${servers[@]}"; do
    echo "Syncing server $server as user $username..."
    ssh "$username@$server" "cd $remote_dir && git pull"
    if [ $? -eq 0 ]; then
        echo "Successfully synced $server"
    else
        echo "Failed to sync $server"
    fi
    echo "------------------------"
done

echo "Sync process completed."

