#!/usr/bin/env python3

import os
import sys
import pwd
import grp
import string
import subprocess
import json
import logging
import argparse
import re
import secrets
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, List
from email_sender import send_email, create_html_email
from cryptography.fernet import Fernet

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to config.json
config_path = os.path.join(script_dir, 'usercreation', 'config.json')

# Open the file
with open(config_path, 'r') as config_file:
    config = json.load(config_file)

# Constants
SFTP_ROOT = config['SFTP_ROOT']
CREDENTIALS_DIR = config['CREDENTIALS_DIR']
ENCRYPTION_KEY = config['ENCRYPTION_KEY'].encode()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Fernet for encryption/decryption
fernet = Fernet(ENCRYPTION_KEY)

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

def validate_username(username: str) -> bool:
    """Validate username format."""
    return bool(re.match(r'^[a-z_][a-z0-9_-]{0,31}$', username))

def generate_password(length: int = 16) -> str:
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    while True:
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        if (any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and sum(c.isdigit() for c in password) >= 3):
            return password

def is_strong_password(password: str) -> bool:
    """Check if the password meets strong password criteria."""
    return (len(password) >= 12 and
            any(c.islower() for c in password) and
            any(c.isupper() for c in password) and
            any(c.isdigit() for c in password) and
            any(c in string.punctuation for c in password))

def get_password() -> str:
    """Get a strong password from user input or generate one."""
    while True:
        password = get_input("Enter a strong password (or press Enter to generate one)")
        if not password:
            return generate_password()
        if is_strong_password(password):
            return password
        print("Password is not strong enough. It must be at least 12 characters long and contain lowercase, uppercase, digits, and special characters.")

def create_user(username: str, password: str, expiration_time: datetime) -> None:
    """Create a new SFTP user with the given username and password."""
    try:
        subprocess.run(['useradd', '-m', '-d', f'{SFTP_ROOT}/{username}', '-s', '/usr/sbin/nologin', '-G', 'sftp', username], check=True)
        subprocess.run(['chpasswd'], input=f'{username}:{password}'.encode(), check=True)
        subprocess.run(['chage', '-E', expiration_time.strftime('%Y-%m-%d'), username], check=True)
        logger.info(f"User {username} created successfully and added to sftp group.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create user {username}: {e}")
        try:
            subprocess.run(['userdel', '-r', username], check=True)
            logger.info(f"Cleaned up failed user creation for {username}")
        except subprocess.CalledProcessError:
            logger.error(f"Failed to clean up after user creation failure for {username}")
        raise RuntimeError(f"Failed to create user {username}")
    except Exception as e:
        logger.error(f"Unexpected error while creating user {username}: {e}")
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
    cron_command = f'{cron_time} userdel -r {username} && rm -rf {SFTP_ROOT}/{username} && rm -f {CREDENTIALS_DIR}/{username}_credentials.enc'
    try:
        current_crontab = subprocess.run(['crontab', '-l'], capture_output=True, text=True, check=True).stdout
        new_crontab = current_crontab + cron_command + '\n'
        subprocess.run(['crontab', '-'], input=new_crontab, text=True, check=True)
        logger.info(f"Scheduled deletion for {username} at {expiration_time}.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to schedule deletion for {username}: {e}")
        raise

def get_department_selection() -> str:
    """Prompt user to select a department from a predefined list."""
    departments = ['Digit', 'El', 'Fjarrvarme', 'Marknad', 'Vatten']
    content = "Select a department:\n" + "\n".join(f"{idx}. {dept}" for idx, dept in enumerate(departments, 1))
    print_box("Department Selection", content)

    while True:
        dept_choice = get_input("Enter the number of the department")
        if dept_choice.isdigit() and 1 <= int(dept_choice) <= len(departments):
            return departments[int(dept_choice) - 1]
        print("║ Invalid choice. Please enter a number from the list.")

def get_user_type() -> str:
    """Get the user type (internal or external)."""
    while True:
        user_type = get_input("Is the user internal (1) or external (2)")
        if user_type in ['1', '2']:
            return "Internal" if user_type == '1' else "External"
        print("Invalid option. Please enter 1 for internal or 2 for external")

def get_deletion_time() -> Optional[timedelta]:
    """Get the deletion time option from user input."""
    options = {
        '1': timedelta(minutes=10),
        '2': timedelta(hours=1),
        '3': timedelta(days=1),
        '4': timedelta(days=30),
        '5': None
    }
    content = "Select user deletion option:\n1. 10 minutes\n2. 1 hour\n3. 1 day\n4. 1 month\n5. No deletion"
    print_box("Deletion Option", content)

    while True:
        choice = get_input("Enter your choice (1-5)")
        if choice in options:
            return options[choice]
        print("Invalid option. Please enter a number between 1 and 5")

def get_user_info() -> Tuple[str, Dict[str, str], Optional[timedelta], str]:
    """Collect user information interactively."""
    clear_screen()
    print_box("User Information", "Please provide the following information:")

    username = get_input("Enter a username")
    while not username or not validate_username(username):
        username = get_input("Invalid username. Please enter a valid username (lowercase letters, numbers, underscore, hyphen, 32 chars max)")

    password = get_password()

    first_name = get_input("Enter first name")
    while not first_name:
        first_name = get_input("First name cannot be empty. Please enter a first name")

    last_name = get_input("Enter last name")
    while not last_name:
        last_name = get_input("Last name cannot be empty. Please enter a last name")

    user_type = get_user_type()

    clear_screen()
    if user_type == "Internal":
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
    deletion_time = get_deletion_time()

    return username, user_info, deletion_time, password

def encrypt_credentials(data: str) -> bytes:
    """Encrypt the given data."""
    return fernet.encrypt(data.encode())

def decrypt_credentials(encrypted_data: bytes) -> str:
    """Decrypt the given encrypted data."""
    return fernet.decrypt(encrypted_data).decode()

def save_credentials(username: str, password: str, user_info: dict, deletion_info: str) -> None:
    """Save encrypted credentials to a file."""
    credentials_file = os.path.join(CREDENTIALS_DIR, f'{username}_credentials.enc')
    credentials_data = json.dumps({
        "username": username,
        "password": password,
        "user_info": user_info,
        "deletion_info": deletion_info
    })
    encrypted_data = encrypt_credentials(credentials_data)
    try:
        with open(credentials_file, 'wb') as f:
            f.write(encrypted_data)
        logger.info(f"Encrypted credentials saved to {credentials_file}")
    except IOError as e:
        logger.error(f"Failed to save encrypted credentials for {username}: {e}")
        raise

def load_credentials(username: str) -> Dict[str, str]:
    """Load and decrypt credentials from a file."""
    credentials_file = os.path.join(CREDENTIALS_DIR, f'{username}_credentials.enc')
    try:
        with open(credentials_file, 'rb') as f:
            encrypted_data = f.read()
        decrypted_data = decrypt_credentials(encrypted_data)
        return json.loads(decrypted_data)
    except IOError as e:
        logger.error(f"Failed to load encrypted credentials for {username}: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse credentials for {username}: {e}")
        raise

def delete_user(username: str) -> None:
    """Delete a user, their home directory, and their credentials file."""
    try:
        subprocess.run(['userdel', '-r', username], check=True)
        credentials_file = os.path.join(CREDENTIALS_DIR, f'{username}_credentials.enc')
        if os.path.exists(credentials_file):
            os.remove(credentials_file)
        logger.info(f"User {username} and their credentials file deleted successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to delete user {username}: {e}")
        raise
    except OSError as e:
        logger.error(f"Failed to delete credentials file for {username}: {e}")

def reset_password(username: str) -> str:
    """Reset password for a given user."""
    new_password = generate_password()
    try:
        subprocess.run(['chpasswd'], input=f'{username}:{new_password}'.encode(), check=True)
        logger.info(f"Password reset for user {username}.")
        return new_password
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to reset password for user {username}: {e}")
        raise

def set_quota(username: str, quota_size: int) -> None:
    """Set quota for a user (in MB)."""
    try:
        subprocess.run(['setquota', '-u', username, '0', str(quota_size * 1024), '0', '0', '/'], check=True)
        logger.info(f"Quota set for user {username}: {quota_size}MB")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to set quota for user {username}: {e}")
        raise

def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="SFTP User Management Tool")
    parser.add_argument('--create', action='store_true', help='Create a new user')
    parser.add_argument('--delete', metavar='USERNAME', help='Delete an existing user')
    parser.add_argument('--reset-password', metavar='USERNAME', help='Reset password for a user')
    parser.add_argument('--set-quota', nargs=2, metavar=('USERNAME', 'QUOTA_MB'), help='Set quota for a user')
    return parser.parse_args()

def create_new_user() -> None:
    """Create a new user with the provided information."""
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

    html_content = create_html_email(f"{username} upplagd på KEAB SFTP", email_content, "Vid frågor, kontakta Digit på it@karlshamnenergi.se.")

    save_credentials(username, password, user_info, deletion_info)

    # Send email to the appropriate recipient and always to it@karlshamnenergi.se
    recipients = [config['IT_EMAIL']]
    if user_info["User Type"] == "Internal":
        recipients.append(user_info["Email"])
    else:  # External user
        recipients.append(user_info["Responsible internally email"])

    send_email(f"Användare {username}", html_content, recipients)

    print_box("User Creation Successful", f"User {username} created successfully.\n{deletion_info}\nCredentials have been saved and sent via email.")

def main() -> None:
    """Main function to handle user management operations."""
    if os.geteuid() != 0:
        logger.error("This script must be run as root.")
        sys.exit(1)

    os.makedirs(CREDENTIALS_DIR, exist_ok=True)

    args = parse_arguments()

    if args.create:
        create_new_user()
    elif args.delete:
        delete_user(args.delete)
        print_box("User Deletion", f"User {args.delete} has been deleted.")
    elif args.reset_password:
        new_password = reset_password(args.reset_password)
        print_box("Password Reset", f"New password for {args.reset_password}: {new_password}")
    elif args.set_quota:
        username, quota_mb = args.set_quota
        set_quota(username, int(quota_mb))
        print_box("Quota Set", f"Quota for {username} set to {quota_mb}MB")
    else:
        while True:
            clear_screen()
            print_box("SFTP User Management", "1. Create User\n2. Delete User\n3. Reset Password\n4. Set Quota\n5. Exit")
            choice = get_input("Enter your choice (1-5)")

            if choice == '1':
                create_new_user()
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
