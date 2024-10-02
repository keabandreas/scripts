#!/usr/bin/env python3

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

# Email configuration
SMTP_SERVER = "karlshamnenergi-se.mail.protection.outlook.com"
SMTP_PORT = 25
FROM_EMAIL = "noreply@karlshamnenergi.se"
TO_EMAIL = "andreas.bergholtz@karlshamnenergi.se"

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def send_error_email(subject: str, error_message: str):
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = FROM_EMAIL
    msg['To'] = TO_EMAIL

    body = f"""
    <html>
    <body>
        <h2 style="color: #D32F2F;">Error Notification</h2>
        <p><strong>Script:</strong> {subject}</p>
        <p><strong>Error Message:</strong></p>
        <pre style="background-color: #FFEBEE; padding: 10px; border-left: 5px solid #D32F2F;">
{error_message}
        </pre>
        <p>Please check the logs for more details.</p>
    </body>
    </html>
    """

    msg.attach(MIMEText(body, 'html'))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.sendmail(FROM_EMAIL, TO_EMAIL, msg.as_string())
        logger.info(f"Error email sent successfully to {TO_EMAIL}")
    except Exception as e:
        logger.error(f"Failed to send error email: {e}")

if __name__ == "__main__":
    # Test the error email functionality
    send_error_email("Test Script", "This is a test error message.")
