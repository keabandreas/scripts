#!/usr/bin/env python3
import os
import shutil
import logging
from datetime import datetime
import requests
from config import SOURCE_DIR, DESTINATION_DIR, LOG_FILE, SLACK_WEBHOOK_URL, ALLOWED_USER

# Set up logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def check_user():
    """Check if the script is being run by the correct user."""
    if os.getlogin() != ALLOWED_USER:
        logging.error(f"This script must be run by the '{ALLOWED_USER}' user.")
        raise PermissionError(f"This script must be run by the '{ALLOWED_USER}' user.")

def move_files():
    """Move files from source to destination directory."""
    moved_files = []
    for filename in os.listdir(SOURCE_DIR):
        if os.path.isfile(os.path.join(SOURCE_DIR, filename)):
            source_file = os.path.join(SOURCE_DIR, filename)
            destination_file = os.path.join(DESTINATION_DIR, filename)
            try:
                shutil.move(source_file, destination_file)
                moved_files.append(filename)
                logging.info(f"Moved file: {filename}")
            except Exception as e:
                logging.error(f"Error moving file {filename}: {str(e)}")
    return moved_files

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
        check_user()
        moved_files = move_files()
        
        if moved_files:
            message = f"Files moved:\n{', '.join(moved_files)}"
        else:
            message = "No files to move."
        
        logging.info(message)
        
        # Read the log file and send its contents to Slack
        with open(LOG_FILE, 'r') as log_file:
            log_contents = log_file.read()
        send_to_slack(f"Fjarrvarme File Movement Log:\n```\n{log_contents}\n```")
        
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        logging.error(error_message)
        send_to_slack(f"Error in Fjarrvarme File Movement Script:\n```\n{error_message}\n```")
        raise

if __name__ == "__main__":
    main()
