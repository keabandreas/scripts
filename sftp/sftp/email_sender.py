#!/usr/bin/env python3

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

# Email configuration
SMTP_SERVER = "karlshamnenergi-se.mail.protection.outlook.com"
SMTP_PORT = 25
FROM_EMAIL = "noreply@karlshamnenergi.se"

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def send_email(subject: str, body: str, to_emails: list):
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

def create_html_email(title: str, content: dict, footer: str = ""):
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ width: 100%; max-width: 600px; margin: 0 auto; }}
            h1 {{ color: #008000; }}  <!-- Changed from #0056b3 to #008000 for green -->
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
    send_email("Test Email", html_content, ["test@example.com", "test2@example.com"])
