#!/bin/bash

# Define source and destination
SOURCE_HOST="digit@172.20.96.22"
SOURCE_DIR="/home/digit/scripts/"
DEST_HOST="172.20.40.247"
DEST_DIR="/home/abe/lib/scripts/work/"

# Perform the rsync
rsync -avz --update ${SOURCE_HOST}:${SOURCE_DIR} ${DEST_DIR}

# Check the exit status
if [ $? -eq 0 ]; then
    echo "Rsync completed successfully."
else
    echo "Rsync encountered an error. Please check the output above for details."
fi
