#!/usr/bin/env python3

import os
import sys
import pwd
import spwd
import crypt
import shutil
import grp
import random
import string
import subprocess
from datetime import datetime, timedelta
import requests
from typing import Dict, Tuple, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
SFTP_ROOT = "/srv/sftp"
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"

def clear_screen():
    """Clear the console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_box(title, content):
    """Print content inside an ASCII box."""
    width = max(len(line) for line in content.split('\n')) + 4
    box_width = max(width, len(title) + 4)

    print("╔" + "═" * (box_width - 2) + "╗")
    print(f"║ {title.center(box_width - 4)} ║")
    print("╠" + "═" * (box_width - 2) + "╣")

    for line in content.split('\n'):
        print(f"║ {line.ljust(box_width - 4)} ║")

    print("╚" + "═" * (box_width - 2) + "╝")

def get_input(prompt):
    """Get user input with a formatted prompt."""
    return input(f"║ {prompt}: ").strip()

def generate_password(length: int = 12) -> str:
    """Generate a random password of specified length."""
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

def create_user(username: str, password: str, expiration_time: datetime) -> None:
    """Create a new SFTP user with the given username and password."""
    try:
        subprocess.run(['useradd', '-m', '-d', f'{SFTP_ROOT}/{username}', '-s', '/usr/sbin/nologin', username], check=True)
        subprocess.run(['chpasswd'], input=f'{username}:{password}'.encode(), check=True)
        subprocess.run(['chage', '-E', expiration_time.strftime('%Y-%m-%d'), username], check=True)
        logger.info(f"User {username} created successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create user {username}: {e}")
        raise

def setup_directory(username: str) -> None:
    """Set up the SFTP directory for the user with appropriate permissions."""
    user_dir = f'{SFTP_ROOT}/{username}'
    try:
        os.makedirs(user_dir, exist_ok=True)
        os.chown(SFTP_ROOT, pwd.getpwnam('root').pw_uid, grp.getgrnam('root').gr_gid)
        os.chown(user_dir, pwd.getpwnam(username).pw_uid, grp.getgrnam(username).gr_gid)
        os.chmod(SFTP_ROOT, 0o755)
        os.chmod(user_dir, 0o700)
        logger.info(f"Directory for {username} set up successfully.")
    except OSError as e:
        logger.error(f"Failed to set up directory for {username}: {e}")
        raise

def remove_bash_files(username: str) -> None:
    """Remove unnecessary bash files from the user's home directory."""
    user_dir = f'{SFTP_ROOT}/{username}'
    bash_files = ['.bash_logout', '.bashrc', '.profile']
    for file in bash_files:
        try:
            os.remove(os.path.join(user_dir, file))
        except FileNotFoundError:
            pass
    logger.info(f"Removed bash files for {username}.")

def schedule_deletion(username: str, expiration_time: datetime) -> None:
    """Schedule the deletion of the user and their data."""
    cron_time = expiration_time.strftime('%M %H %d %m *')
    cron_command = f'{cron_time} userdel -r {username} && rm -rf {SFTP_ROOT}/{username} && rm -f /root/{username}_credentials.txt'
    try:
        current_crontab = subprocess.run(['crontab', '-l'], capture_output=True, text=True, check=True).stdout
        new_crontab = current_crontab + cron_command + '\n'
        subprocess.run(['crontab', '-'], input=new_crontab, text=True, check=True)
        logger.info(f"Scheduled deletion for {username} at {expiration_time}.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to schedule deletion for {username}: {e}")
        raise

def send_slack_notification(message: str) -> None:
    """Send a notification to Slack using the webhook URL."""
    payload = {"text": message}
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        logger.info("Slack notification sent successfully.")
    except requests.RequestException as e:
        logger.error(f"Failed to send Slack notification: {e}")
        raise

def get_department_selection():
    """Prompt user to select a department from a predefined list."""
    departments = ['Digit', 'El', 'Fjarrvarme', 'Marknad', 'Vatten']
    content = "Select a department:\n" + "\n".join(f"{idx}. {dept}" for idx, dept in enumerate(departments, 1))
    print_box("Department Selection", content)

    while True:
        dept_choice = get_input("Enter the number of the department")
        if dept_choice.isdigit() and 1 <= int(dept_choice) <= len(departments):
            return departments[int(dept_choice) - 1]
        print("║ Invalid choice. Please enter a number from the list.")

def get_user_info() -> Tuple[str, Dict[str, str], Optional[timedelta]]:
    """Collect user information interactively."""
    clear_screen()
    print_box("User Information", "Please provide the following information:")

    username = get_input("Enter a username")
    while not username:
        username = get_input("Username cannot be empty. Please enter a username")

    first_name = get_input("Enter first name")
    while not first_name:
        first_name = get_input("First name cannot be empty. Please enter a first name")

    last_name = get_input("Enter last name")
    while not last_name:
        last_name = get_input("Last name cannot be empty. Please enter a last name")

    user_type = get_input("Is the user internal (1) or external (2)")
    while user_type not in ['1', '2']:
        user_type = get_input("Invalid option. Please enter 1 for internal or 2 for external")

    clear_screen()
    if user_type == '1':
        department = get_department_selection()
        email = f"{first_name.lower()}.{last_name.lower()}@karlshamnenergi.se"
        user_info = {
            "First name": first_name,
            "Last name": last_name,
            "Department": department,
            "Email": email
        }
    else:
        print_box("External User Information", "Please provide the following information:")
        company = get_input("Enter company")
        karlshamn_department = get_department_selection()
        superior_first_name = get_input("Enter superior's first name")
        while not superior_first_name:
            superior_first_name = get_input("Superior's first name cannot be empty. Please enter a first name")
        superior_last_name = get_input("Enter superior's last name")
        while not superior_last_name:
            superior_last_name = get_input("Superior's last name cannot be empty. Please enter a last name")
        superior_email = f"{superior_first_name.lower()}.{superior_last_name.lower()}@karlshamnenergi.se"
        user_info = {
            "First name": first_name,
            "Last name": last_name,
            "Company": company,
            "Handled by department": karlshamn_department,
            "Superior first name": superior_first_name,
            "Superior last name": superior_last_name,
            "Superior email": superior_email
        }

    clear_screen()
    content = "Select user deletion option:\n1. 10 minutes\n2. 1 hour\n3. 1 day\n4. 1 month\n5. No deletion"
    print_box("Deletion Option", content)

    deletion_option = get_input("Enter your choice (1-5)")
    while deletion_option not in ['1', '2', '3', '4', '5']:
        deletion_option = get_input("Invalid option. Please enter a number between 1 and 5")

    deletion_time = None
    if deletion_option == '1':
        deletion_time = timedelta(minutes=10)
    elif deletion_option == '2':
        deletion_time = timedelta(hours=1)
    elif deletion_option == '3':
        deletion_time = timedelta(days=1)
    elif deletion_option == '4':
        deletion_time = timedelta(days=30)
    # For option '5', deletion_time remains None

    return username, user_info, deletion_time

def delete_user(username):
    """Delete a user and their home directory."""
    try:
        subprocess.run(['userdel', '-r', username], check=True)
        logger.info(f"User {username} deleted successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to delete user {username}: {e}")
        raise

def reset_password(username):
    """Reset password for a given user."""
    new_password = generate_password()
    try:
        subprocess.run(['chpasswd'], input=f'{username}:{new_password}'.encode(), check=True)
        logger.info(f"Password reset for user {username}.")
        return new_password
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to reset password for user {username}: {e}")
        raise

def set_quota(username, quota_size):
    """Set quota for a user (in MB)."""
    try:
        subprocess.run(['setquota', '-u', username, '0', str(quota_size * 1024), '0', '0', '/'], check=True)
        logger.info(f"Quota set for user {username}: {quota_size}MB")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to set quota for user {username}: {e}")
        raise

def main():
    if os.geteuid() != 0:
        logger.error("This script must be run as root.")
        sys.exit(1)

    while True:
        clear_screen()
        print_box("SFTP User Management", "1. Create User\n2. Delete User\n3. Reset Password\n4. Set Quota\n5. Exit")
        choice = get_input("Enter your choice (1-5)")

        if choice == '1':
            # Existing user creation logic
            username, user_info, deletion_time = get_user_info()
            password = generate_password()
            create_user(username, password, datetime.max if deletion_time is None else datetime.now() + deletion_time)
            setup_directory(username)
            remove_bash_files(username)
            
            # Schedule deletion if a deletion time was chosen
            if deletion_time:
                expiration_time = datetime.now() + deletion_time
                schedule_deletion(username, expiration_time)
                deletion_info = f"The user will be removed along with data at {expiration_time}."
            else:
                deletion_info = "The user account has no scheduled deletion."

            # Prepare credentials information
            credentials = [f"{k}: {v}" for k, v in user_info.items()]
            credentials.extend([
                f"Username: {username}",
                f"Password: {password}",
                f"User directory: {SFTP_ROOT}/{username}",
                deletion_info
            ])
            credentials_str = "\n".join(credentials)

            # Save credentials to a file
            with open(f'/root/{username}_credentials.txt', 'w') as f:
                f.write(credentials_str)

            # Send Slack notification with user credentials
            slack_message = f"New SFTP User Created:\n{credentials_str}"
            send_slack_notification(slack_message)

            print_box("User Creation Successful", f"User {username} created successfully.\n{deletion_info}\nCredentials have been sent via Slack.")

        elif choice == '2':
            username = get_input("Enter username to delete")
            if username:
                delete_user(username)
                print_box("User Deletion", f"User {username} has been deleted.")

        elif choice == '3':
            username = get_input("Enter username to reset password")
            if username:
                new_password = reset_password(username)
                print_box("Password Reset", f"New password for {username}: {new_password}")

        elif choice == '4':
            username = get_input("Enter username to set quota")
            if username:
                quota_size = get_input("Enter quota size in MB")
                if quota_size.isdigit():
                    set_quota(username, int(quota_size))
                    print_box("Quota Set", f"Quota for {username} set to {quota_size}MB")
                else:
                    print("Invalid quota size. Please enter a number.")

        elif choice == '5':
            print_box("Goodbye", "Exiting the script.")
            break

        else:
            print("Invalid choice. Please try again.")

        input("Press Enter to continue...")

if __name__ == "__main__":
    main()
