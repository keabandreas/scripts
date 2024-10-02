#!/usr/bin/env python3

import os
import sys
import pwd
import grp
import random
import string
import subprocess
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import logging
from email_sender import send_email, create_html_email

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
SFTP_ROOT = "/srv/sftp"
CREDENTIALS_DIR = "/root/credentials"

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
        subprocess.run(['useradd', '-m', '-d', f'{SFTP_ROOT}/{username}', '-s', '/usr/sbin/nologin', '-G', 'sftp', username], check=True)
        subprocess.run(['chpasswd'], input=f'{username}:{password}'.encode(), check=True)
        subprocess.run(['chage', '-E', expiration_time.strftime('%Y-%m-%d'), username], check=True)
        logger.info(f"User {username} created successfully and added to sftp group.")
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
    cron_command = f'{cron_time} userdel -r {username} && rm -rf {SFTP_ROOT}/{username} && rm -f {CREDENTIALS_DIR}/{username}_credentials.txt'
    try:
        current_crontab = subprocess.run(['crontab', '-l'], capture_output=True, text=True, check=True).stdout
        new_crontab = current_crontab + cron_command + '\n'
        subprocess.run(['crontab', '-'], input=new_crontab, text=True, check=True)
        logger.info(f"Scheduled deletion for {username} at {expiration_time}.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to schedule deletion for {username}: {e}")
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

def get_user_info() -> Tuple[str, Dict[str, str], Optional[timedelta], str]:
    """Collect user information interactively."""
    clear_screen()
    print_box("User Information", "Please provide the following information:")

    username = get_input("Enter a username")
    while not username:
        username = get_input("Username cannot be empty. Please enter a username")

    password_option = get_input("Choose password option: (1) Fill password, (2) Randomize password")
    while password_option not in ['1', '2']:
        password_option = get_input("Invalid option. Please enter 1 to fill password or 2 to randomize")

    if password_option == '1':
        password = get_input("Enter password")
        while not password:
            password = get_input("Password cannot be empty. Please enter a password")
    else:
        password = generate_password()

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
            "Email": email,
            "User Type": "Internal"
        }
    else:
        print_box("External User Information", "Please provide the following information:")
        company = get_input("Enter company")
        karlshamn_department = get_department_selection()
        responsible_first_name = get_input("Enter responsible internally's first name")
        while not responsible_first_name:
            responsible_first_name = get_input("Responsible internally's first name cannot be empty. Please enter a first name")
        responsible_last_name = get_input("Enter responsible internally's last name")
        while not responsible_last_name:
            responsible_last_name = get_input("Responsible internally's last name cannot be empty. Please enter a last name")
        responsible_email = f"{responsible_first_name.lower()}.{responsible_last_name.lower()}@karlshamnenergi.se"
        user_info = {
            "First name": first_name,
            "Last name": last_name,
            "Company": company,
            "Handled by department": karlshamn_department,
            "Responsible internally first name": responsible_first_name,
            "Responsible internally last name": responsible_last_name,
            "Responsible internally email": responsible_email,
            "User Type": "External"
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

    return username, user_info, deletion_time, password

def delete_user(username):
    """Delete a user, their home directory, and their credentials file."""
    try:
        subprocess.run(['userdel', '-r', username], check=True)
        credentials_file = os.path.join(CREDENTIALS_DIR, f'{username}_credentials.txt')
        if os.path.exists(credentials_file):
            os.remove(credentials_file)
        logger.info(f"User {username} and their credentials file deleted successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to delete user {username}: {e}")
        raise
    except OSError as e:
        logger.error(f"Failed to delete credentials file for {username}: {e}")

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

    os.makedirs(CREDENTIALS_DIR, exist_ok=True)

    while True:
        clear_screen()
        print_box("SFTP User Management", "1. Create User\n2. Delete User\n3. Reset Password\n4. Set Quota\n5. Exit")
        choice = get_input("Enter your choice (1-5)")

        if choice == '1':
            username, user_info, deletion_time, password = get_user_info()
            create_user(username, password, datetime.max if deletion_time is None else datetime.now() + deletion_time)
            setup_directory(username)
            remove_bash_files(username)

            if deletion_time:
                expiration_time = datetime.now() + deletion_time
                schedule_deletion(username, expiration_time)
                deletion_info = f"The user will be removed along with data at {expiration_time}."
            else:
                deletion_info = "The user account has no scheduled deletion."

            user_directory = f"{SFTP_ROOT}/{username}"

            email_content = {
                "Username": username,
                "Password": password,
                "User Directory": user_directory,
                "Deletion Info": deletion_info,
                "User Type": user_info["User Type"]
            }
            email_content.update(user_info)

            html_content = create_html_email(f"{USERNAME} upplagd på KEAB SFTP", email_content, "Vid frågor, kontakta Digit på it@karlshamnenergi.se.")

            credentials_file = os.path.join(CREDENTIALS_DIR, f'{username}_credentials.txt')
            with open(credentials_file, 'w') as f:
                f.write(html_content)

            # Send email to the appropriate recipient and always to it@karlshamnenergi.se
            recipients = ["it@karlshamnenergi.se"]
            if user_info["User Type"] == "Internal":
                recipients.append(user_info["Email"])
            else:  # External user
                recipients.append(user_info["Responsible internally email"])

            send_email(f"Användare {USERNAME}", html_content, recipients)

            print_box("User Creation Successful", f"User {username} created successfully.\n{deletion_info}\nCredentials have been saved to {credentials_file} and sent via email.")

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