import logging
import os
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)


def send_email(to_address, subject, body):
    """Send an email when SMTP is configured; return False otherwise."""
    host = os.getenv('MAIL_SERVER')
    if not host:
        return False
    port = int(os.getenv('MAIL_PORT', '587'))
    username = os.getenv('MAIL_USERNAME')
    password = os.getenv('MAIL_PASSWORD')
    sender = os.getenv('MAIL_DEFAULT_SENDER', username or 'no-reply@matchflow.cm')
    message = EmailMessage()
    message['Subject'] = subject
    message['From'] = sender
    message['To'] = to_address
    message.set_content(body)
    try:
        with smtplib.SMTP(host, port, timeout=15) as server:
            if os.getenv('MAIL_USE_TLS', '1') == '1':
                server.starttls()
            if username and password:
                server.login(username, password)
            server.send_message(message)
        return True
    except (OSError, smtplib.SMTPException):
        logger.exception('SMTP delivery failed')
        return False
