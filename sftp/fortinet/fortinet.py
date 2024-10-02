#!/usr/bin/env python3

import os
import shutil
import time
from datetime import datetime
import logging
from pathlib import Path
import json

# Load configuration
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'config.json')
with open(config_path, 'r') as config_file:
    config = json.load(config_file)

# Set up logging
LOG_FILE = config['log_file']
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Constants
FORTINET_HOME = Path(config['fortinet_home'])
DATE = datetime.now().strftime("%Y%m%d")
PROCESS_FOLDER = FORTINET_HOME / "fortigate" / "PROCESS" / DATE
FORTIGATE_FOLDER = FORTINET_HOME / "fortigate" / "FORTIGATE" / DATE
ANALYZER_FOLDER = FORTINET_HOME / "analyzer"
RETENTION_DAYS = config['retention_days']

def create_directories():
    """Create necessary directories."""
    for folder in [PROCESS_FOLDER, FORTIGATE_FOLDER, ANALYZER_FOLDER]:
        folder.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created directory: {folder}")

def add_date_to_files():
    """Add date to files ending with _KEAB-FG.conf or _PROC-FG.conf."""
    for pattern in ['*_KEAB-FG.conf', '*_PROC-FG.conf']:
        for file in FORTINET_HOME.glob(pattern):
            if file.is_file():
                new_name = file.with_name(f"{file.stem}_{DATE}{file.suffix}")
                file.rename(new_name)
                logging.info(f"Renamed {file} to {new_name}")

def move_files():
    """Move files to appropriate folders based on their names."""
    for file in FORTINET_HOME.glob('*.conf'):
        if file.is_file():
            if '_KEAB-FG_' in file.name:
                destination = FORTIGATE_FOLDER
            elif '_PROC-FG_' in file.name:
                destination = PROCESS_FOLDER
            else:
                logging.warning(f"Unrecognized file pattern: {file.name}")
                continue

            shutil.move(str(file), str(destination))
            logging.info(f"Moved {file} to {destination}")

def delete_old_files():
    """Delete files and directories older than the configured number of days."""
    cutoff_time = time.time() - (RETENTION_DAYS * 24 * 60 * 60)

    # Delete old directories in PROCESS and FORTIGATE folders
    for folder in [FORTINET_HOME / "fortigate" / "PROCESS", FORTINET_HOME / "fortigate" / "FORTIGATE"]:
        for item in folder.iterdir():
            if item.is_dir() and item.stat().st_mtime < cutoff_time:
                shutil.rmtree(item)
                logging.info(f"Deleted old directory: {item}")

    # Delete old files in ANALYZER folder
    for file in ANALYZER_FOLDER.glob('*'):
        if file.is_file() and file.stat().st_mtime < cutoff_time:
            file.unlink()
            logging.info(f"Deleted old file: {file}")

def main():
    try:
        create_directories()
        add_date_to_files()
        move_files()
        delete_old_files()
        logging.info("Script completed successfully")

    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        logging.error(error_message)

if __name__ == "__main__":
    main()
