import os
import smtplib
from email.message import EmailMessage


def send_email(to_email: str, subject: str, body: str):
    email_enabled = os.getenv("EMAIL_ENABLED", "false").lower() == "true"

    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER") or os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    from_name = os.getenv("FROM_NAME", "DevSpace One")
    from_email = os.getenv("FROM_EMAIL") or smtp_user

    if not email_enabled:
        print("EMAIL DISABLED - Preview only")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(body)
        return False

    if not smtp_user:
        raise ValueError("SMTP_USER or SMTP_USERNAME is missing")

    if not smtp_password:
        raise ValueError("SMTP_PASSWORD is missing")

    if not to_email:
        raise ValueError("ALERT_TO_EMAIL / to_email is missing")

    msg = EmailMessage()
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)

    print(f"Email sent to {to_email}")
    return True
