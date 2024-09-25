#!/usr/bin/env python3

import os
import shutil
import time
from datetime import datetime
import logging
from pathlib import Path
import requests
import glob

# Set up logging
LOG_FILE = os.path.expanduser('~/fortinet_file_operations.log')
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Constants
FORTINET_HOME = Path("/home/fortinet")
DATE = datetime.now().strftime("%Y%m%d")
PROCESS_FOLDER = FORTINET_HOME / "fortigate" / "PROCESS" / DATE
FORTIGATE_FOLDER = FORTINET_HOME / "fortigate" / "FORTIGATE" / DATE
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"

def create_directories():
    """Create necessary directories."""
    for folder in [PROCESS_FOLDER, FORTIGATE_FOLDER]:
        folder.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created directory: {folder}")

def remove_conf_extension():
    """Remove .conf extension from files."""
    for file in FORTINET_HOME.glob('*.conf'):
        new_name = file.with_suffix('')
        file.rename(new_name)
        logging.info(f"Renamed {file} to {new_name}")

def add_date_to_files():
    """Add date to FG* and PROC* files."""
    for pattern in ['FG*', 'PROC*']:
        for file in FORTINET_HOME.glob(pattern):
            if file.is_file():
                new_name = file.with_name(f"{file.name}_{DATE}.conf")
                file.rename(new_name)
                logging.info(f"Renamed {file} to {new_name}")

def move_files():
    """Move files to appropriate folders."""
    for file in FORTINET_HOME.glob('PROC*'):
        if file.is_file():
            shutil.move(str(file), str(PROCESS_FOLDER))
            logging.info(f"Moved {file} to {PROCESS_FOLDER}")

    for file in FORTINET_HOME.glob('FG*'):
        if file.is_file():
            shutil.move(str(file), str(FORTIGATE_FOLDER))
            logging.info(f"Moved {file} to {FORTIGATE_FOLDER}")

def check_file_transfer():
    """Check if new files have been fully transferred."""
    logging.info("Checking for file transfer completion...")
    
    # Wait for a short period to ensure transfer has started
    time.sleep(10)
    
    # Check file sizes multiple times to ensure they're not changing
    for _ in range(3):
        sizes = {}
        for folder in [PROCESS_FOLDER, FORTIGATE_FOLDER]:
            for file in folder.glob('*'):
                sizes[file] = file.stat().st_size
        
        time.sleep(5)  # Wait before checking again
        
        # Compare sizes
        all_stable = True
        for file, size in sizes.items():
            if file.stat().st_size != size:
                all_stable = False
                break
        
        if all_stable:
            logging.info("File transfer completed.")
            return True
    
    logging.warning("File transfer may not be complete.")
    return False

def process_files():
    """Process files according to the bash script logic."""
    # Remove .conf extension
    for file in glob.glob(f"{FORTINET_HOME}/*.conf"):
        os.rename(file, os.path.splitext(file)[0])
        logging.info(f"Removed .conf extension from {file}")

    # Add date to FG* and PROC* files
    for pattern in ['FG*', 'PROC*']:
        for file in glob.glob(f"{FORTINET_HOME}/{pattern}"):
            new_name = f"{file}_{DATE}.conf"
            os.rename(file, new_name)
            logging.info(f"Renamed {file} to {new_name}")

    # Create directories
    os.makedirs(PROCESS_FOLDER, exist_ok=True)
    os.makedirs(FORTIGATE_FOLDER, exist_ok=True)
    logging.info(f"Created directories: {PROCESS_FOLDER}, {FORTIGATE_FOLDER}")

    # Move files
    for file in glob.glob(f"{os.path.expanduser('~')}/PROC*"):
        shutil.move(file, PROCESS_FOLDER)
        logging.info(f"Moved {file} to {PROCESS_FOLDER}")

    for file in glob.glob(f"{os.path.expanduser('~')}/FG*"):
        shutil.move(file, FORTIGATE_FOLDER)
        logging.info(f"Moved {file} to {FORTIGATE_FOLDER}")

def send_to_slack(message):
    """Send a message to Slack."""
    payload = {"text": message}
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        logging.info("Log sent to Slack successfully.")
    except requests.RequestException as e:
        logging.error(f"Failed to send log to Slack: {e}")

def main():
    try:
        create_directories()
        remove_conf_extension()
        add_date_to_files()
        move_files()
        
        if check_file_transfer():
            process_files()
        else:
            logging.warning("Skipping file processing due to incomplete file transfer.")
        
        logging.info("Script completed successfully")
        
        # Read the log file and send its contents to Slack
        with open(LOG_FILE, 'r') as log_file:
            log_contents = log_file.read()
        send_to_slack(f"Fortinet File Management Log:\n```\n{log_contents}\n```")
        
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        logging.error(error_message)
        send_to_slack(f"Error in Fortinet File Management Script:\n```\n{error_message}\n```")
        raise

if __name__ == "__main__":
    main()
