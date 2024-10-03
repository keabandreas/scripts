#!/usr/bin/env python3
import os
import shutil
import logging
from datetime import datetime
import json

# Load configuration
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'config.json')
with open(config_path, 'r') as config_file:
    config = json.load(config_file)

# Configuration
SOURCE_DIR = config['source_dir']
DESTINATION_DIRS = config['destination_dirs']
LOG_FILE = config['log_file']

# Set up logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def move_files():
    """Move files from source to destination directories based on file names."""
    moved_files = []
    for filename in os.listdir(SOURCE_DIR):
        if os.path.isfile(os.path.join(SOURCE_DIR, filename)):
            source_file = os.path.join(SOURCE_DIR, filename)
            destination_dir = None

            for prefix, dest_dir in DESTINATION_DIRS.items():
                if filename.startswith(prefix):
                    destination_dir = dest_dir
                    break

            if destination_dir:
                destination_file = os.path.join(destination_dir, filename)
                try:
                    shutil.move(source_file, destination_file)
                    moved_files.append(f"{filename} -> {destination_dir}")
                    logging.info(f"Moved file: {filename} to {destination_dir}")
                except Exception as e:
                    logging.error(f"Error moving file {filename}: {str(e)}")
            else:
                logging.warning(f"No matching destination for file: {filename}")

    return moved_files

def main():
    try:
        moved_files = move_files()

        if moved_files:
            message = "Files moved:\n" + "\n".join(moved_files)
        else:
            message = "No files to move."

        logging.info(message)

    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        logging.error(error_message)
        # Error is logged but no email is sent

if __name__ == "__main__":
    main()
