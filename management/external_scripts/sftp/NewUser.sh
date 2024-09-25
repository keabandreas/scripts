#!/bin/bash

# Read configuration from JSON file
config_file="NewUser.json"
ssh_user=$(jq -r '.ssh_user' "$config_file")
ssh_host=$(jq -r '.ssh_host' "$config_file")
script_path=$(jq -r '.script_path' "$config_file")

# SSH into the specified host
ssh "${ssh_user}@${ssh_host}" << EOF
    # Run the Python script with sudo
    sudo python3 \$HOME${script_path}
    
    # Exit the SSH session
    exit
EOF
# Exit the local script
exit 0
