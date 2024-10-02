#!/usr/bin/env python3

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import os
import json
from typing import List, Dict
from dotenv import load_dotenv

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to config.json
config_path = os.path.join(script_dir, 'email', 'config.json')

# Open the file and load the JSON data
with open(config_path, 'r') as config_file:
    config = json.load(config_file)

# Load environment variables
load_dotenv()

# Email configuration
SMTP_SERVER = os.environ.get("SMTP_SERVER", config.get("SMTP_SERVER"))
SMTP_PORT = int(os.environ.get("SMTP_PORT", config.get("SMTP_PORT", 25)))
FROM_EMAIL = os.environ.get("FROM_EMAIL", config.get("FROM_EMAIL"))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def send_email(subject: str, body: str, to_emails: List[str]) -> None:
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = FROM_EMAIL
    msg['To'] = ', '.join(to_emails)  # Join multiple email addresses

    text_part = MIMEText(body, 'plain')
    html_part = MIMEText(body, 'html')

    msg.attach(text_part)
    msg.attach(html_part)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.sendmail(FROM_EMAIL, to_emails, msg.as_string())
        logger.info(f"Email sent successfully to {', '.join(to_emails)}")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise

def create_html_email(title: str, content: Dict[str, str], footer: str = "") -> str:
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ width: 100%; max-width: 600px; margin: 0 auto; }}
            h1 {{ color: #008000; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .footer {{ margin-top: 20px; font-style: italic; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{title}</h1>
            <table>
    """
    
    for key, value in content.items():
        html += f"<tr><th>{key}</th><td>{value}</td></tr>"
    
    html += f"""
            </table>
            <p class="footer">{footer}</p>
        </div>
    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    # Test the email sending functionality
    test_content = {
        "Test Key 1": "Test Value 1",
        "Test Key 2": "Test Value 2"
    }
    html_content = create_html_email("Test Email", test_content, "This is a test email.")
    
    # Write test content to a temporary file
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        temp_file.write(html_content)
    
    # Send email with the content from the file
    with open(temp_file.name, 'r') as file:
        send_email("Test Email", file.read(), ["test@example.com", "test2@example.com"])
    
    # Clean up the temporary file
    os.unlink(temp_file.name)
