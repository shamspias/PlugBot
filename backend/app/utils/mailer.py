import smtplib, ssl
from email.message import EmailMessage
from ..core.config import settings


def send_email(to_email: str, subject: str, body: str):
    if not settings.SMTP_HOST:
        raise RuntimeError("SMTP not configured")

    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    context = ssl.create_default_context()
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_STARTTLS:
            server.starttls(context=context)
        if settings.SMTP_USERNAME:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(msg)
