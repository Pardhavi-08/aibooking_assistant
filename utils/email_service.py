# email_service.py
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


def send_confirmation_email(booking_data: dict):
    sender_email = EMAIL_SENDER
    receiver_email = booking_data["email"]

    clinic_name = str(booking_data.get("clinic", "Clinic"))
    name = booking_data.get("name", "")
    service = booking_data.get("service", "")
    date = booking_data.get("date", "")
    time = booking_data.get("time", "")

    subject = f"Appointment Confirmed – {clinic_name}"

    body = f"""
Hello {name},

Your appointment has been successfully confirmed. ✅

📍 Clinic: {clinic_name}
🩺 Service: {service}
📅 Date: {date}
⏰ Time: {time}

Please arrive 10 minutes early and carry any relevant medical records.

Regards,
{clinic_name}
"""

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print("❌ EMAIL ERROR:", e)
        raise
