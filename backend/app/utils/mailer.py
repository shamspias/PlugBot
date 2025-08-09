import smtplib
import ssl
from email.message import EmailMessage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..core.config import settings


def send_email(to_email: str, subject: str, body: str, html_body: str = None):
    """Send email with optional HTML content."""
    if not settings.SMTP_HOST:
        raise RuntimeError("SMTP not configured")

    # Create message
    if html_body:
        # Send multipart message with HTML and plain text
        msg = MIMEMultipart('alternative')
        msg['From'] = settings.SMTP_FROM
        msg['To'] = to_email
        msg['Subject'] = subject

        # Add plain text part
        text_part = MIMEText(body, 'plain')
        msg.attach(text_part)

        # Add HTML part
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
    else:
        # Send plain text only
        msg = EmailMessage()
        msg['From'] = settings.SMTP_FROM
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.set_content(body)

    # Send email
    context = ssl.create_default_context()
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_STARTTLS:
            server.starttls(context=context)
        if settings.SMTP_USERNAME:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)

        if html_body:
            server.send_message(msg)
        else:
            server.send_message(msg)
