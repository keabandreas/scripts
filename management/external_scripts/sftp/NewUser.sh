#!/bin/bash

# SSH into the specified host
ssh digit@172.20.96.22 << EOF
    # Run the Python script with sudo
    sudo python3 \$HOME/digit/scripts/useradd.py
    
    # Exit the SSH session
    exit
EOF

# Exit the local script
exit 0
