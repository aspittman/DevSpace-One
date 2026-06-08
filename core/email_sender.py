import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()


def send_email(to_email: str, subject: str, body: str):
    if os.getenv("EMAIL_ENABLED", "false").lower() != "true":
        print("EMAIL DISABLED - Preview only")
        print("TO:", to_email)
        print("SUBJECT:", subject)
        print(body)
        return {"sent": False, "preview": True}

    msg = EmailMessage()
    msg["From"] = os.getenv("SMTP_USER")
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT", "587"))) as server:
        server.starttls()
        server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD"))
        server.send_message(msg)

    return {"sent": True}