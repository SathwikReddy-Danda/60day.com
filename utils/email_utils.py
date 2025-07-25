import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

SENDER_EMAIL = os.environ["EMAIL_SENDER"]  # <-- replace with your Gmail
APP_PASSWORD = os.environ["EMAIL_PASSWORD"]    # <-- replace with your App Password

def send_recruiter_notification(to_email, job_title, candidate_name, message, resume_bytes=None, resume_filename="resume.pdf"):
    subject = "New applicant for job posting"
    body = f"""
Hello,

A new candidate has applied to your job posting: "{job_title}".

Candidate Name: {candidate_name}
Message: {message}

Please log in to 60day.com to view full application details.

Thanks,  
60day.com Bot
"""

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject

    # Add plain text
    msg.attach(MIMEText(body, "plain"))

    # Add resume if available
    if resume_bytes:
        attachment = MIMEApplication(resume_bytes, _subtype="pdf")
        attachment.add_header('Content-Disposition', 'attachment', filename=resume_filename)
        msg.attach(attachment)

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.send_message(msg)
        print("✅ Email with resume sent to recruiter.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
