import logging
import random
import string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import aiosmtplib

from backend.config import settings

logger = logging.getLogger("taskflow.email")

def generate_pin_code(length: int = 6) -> str:
    """Generate a random 6-digit numeric verification code."""
    return "".join(random.choices(string.digits, k=length))

async def send_email(to_email: str, subject: str, html_content: str, text_content: str) -> bool:
    """Sends email via SMTP or falls back to development logging."""
    smtp_user = (settings.SMTP_USER or "").strip()
    smtp_password = (settings.SMTP_PASSWORD or "").replace(" ", "").strip()
    sender_email = (settings.SMTP_FROM_EMAIL or smtp_user).strip()

    # If SMTP is not fully configured, log to console for dev ease
    if not smtp_user or not smtp_password:
        logger.info(f"[DEV EMAIL LOG] To: {to_email} | Subject: {subject}\n{text_content}")
        print(f"\n========================================================")
        print(f"📧 [TASKFLOW EMAIL NOTIFICATION - SENDER: {sender_email}]")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(f"Content:\n{text_content}")
        print(f"========================================================\n")
        return True

    message = MIMEMultipart("alternative")
    message["From"] = f"{settings.SMTP_FROM_NAME} <{sender_email}>"
    message["To"] = to_email
    message["Subject"] = subject

    part1 = MIMEText(text_content, "plain")
    part2 = MIMEText(html_content, "html")
    message.attach(part1)
    message.attach(part2)

    # Force only Port 465 SSL (Gmail) – no other ports attempted on Render
    ports_to_try = [(465, True)]
    seen = set()
    unique_ports = []
    for p, ssl in ports_to_try:
        if p not in seen:
            seen.add(p)
            unique_ports.append((p, ssl))

    last_error = None
    for port, use_ssl in unique_ports:
        try:
            await aiosmtplib.send(
                message,
                sender=sender_email,
                recipients=[to_email],
                hostname=settings.SMTP_HOST,
                port=port,
                use_tls=use_ssl,
                start_tls=(not use_ssl),
                username=smtp_user,
                password=smtp_password,
                timeout=12,
            )
            logger.info(f"Email successfully dispatched to {to_email} via {settings.SMTP_HOST}:{port}")
            return True
        except Exception as e:
            last_error = e
            logger.warning(f"SMTP attempt on {settings.SMTP_HOST}:{port} failed: {e}")

    logger.error(f"All SMTP attempts failed for {to_email}. Last error: {last_error}")
    print(f"\n[SMTP FAILED - CONSOLE FALLBACK] Code for {to_email}:\n{text_content}\n")
    return False

async def send_verification_email(to_email: str, full_name: str, code: str):
    """Sends 6-digit email verification code."""
    subject = f"Verify your TaskFlow account - {code}"
    
    text_content = (
        f"Hello {full_name},\n\n"
        f"Thank you for registering at TaskFlow! Your email verification code is:\n\n"
        f"    {code}\n\n"
        f"This code will expire in {settings.VERIFICATION_CODE_EXPIRE_MINUTES} minutes.\n"
        f"Please enter this code on the verification screen to activate your account.\n\n"
        f"Best regards,\nThe TaskFlow Team"
    )

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: 'Quicksand', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #1e293b; }}
        .card {{ max-width: 500px; margin: 0 auto; background: #ffffff; border-radius: 16px; padding: 32px; box-shadow: 0 4px 20px rgba(0,0,0,0.06); border: 1px solid #e2e8f0; }}
        .header {{ text-align: center; margin-bottom: 24px; }}
        .logo {{ font-size: 28px; font-weight: 700; color: #4f46e5; letter-spacing: -0.5px; }}
        .code-box {{ background: #f1f5f9; border-radius: 12px; padding: 18px; text-align: center; font-size: 32px; font-weight: 700; letter-spacing: 8px; color: #4f46e5; margin: 24px 0; border: 2px dashed #c7d2fe; }}
        .footer {{ font-size: 13px; color: #94a3b8; text-align: center; margin-top: 24px; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="header">
          <div class="logo">⚡ TaskFlow</div>
          <h2 style="font-size: 20px; color: #0f172a; margin-top: 8px;">Verify Your Email Address</h2>
        </div>
        <p>Hi <strong>{full_name}</strong>,</p>
        <p>Thank you for signing up for TaskFlow! Please use the 6-digit verification code below to activate your account:</p>
        <div class="code-box">{code}</div>
        <p style="font-size: 14px; color: #64748b;">This verification code will expire in <strong>{settings.VERIFICATION_CODE_EXPIRE_MINUTES} minutes</strong>. If you did not create a TaskFlow account, please ignore this email.</p>
        <div class="footer">
          &copy; TaskFlow - Smart Task Manager with Real-time Deadlines
        </div>
      </div>
    </body>
    </html>
    """

    await send_email(to_email, subject, html_content, text_content)

async def send_password_reset_email(to_email: str, full_name: str, code: str):
    """Sends 6-digit password reset code."""
    subject = f"Reset your TaskFlow password - {code}"
    
    text_content = (
        f"Hello {full_name},\n\n"
        f"We received a request to reset the password for your TaskFlow account.\n\n"
        f"Your password reset code is:\n\n"
        f"    {code}\n\n"
        f"This code will expire in {settings.VERIFICATION_CODE_EXPIRE_MINUTES} minutes.\n"
        f"If you did not request a password reset, you can safely disregard this message.\n\n"
        f"Best regards,\nThe TaskFlow Team"
    )

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: 'Quicksand', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #1e293b; }}
        .card {{ max-width: 500px; margin: 0 auto; background: #ffffff; border-radius: 16px; padding: 32px; box-shadow: 0 4px 20px rgba(0,0,0,0.06); border: 1px solid #e2e8f0; }}
        .header {{ text-align: center; margin-bottom: 24px; }}
        .logo {{ font-size: 28px; font-weight: 700; color: #4f46e5; letter-spacing: -0.5px; }}
        .code-box {{ background: #fef2f2; border-radius: 12px; padding: 18px; text-align: center; font-size: 32px; font-weight: 700; letter-spacing: 8px; color: #ef4444; margin: 24px 0; border: 2px dashed #fecaca; }}
        .footer {{ font-size: 13px; color: #94a3b8; text-align: center; margin-top: 24px; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="header">
          <div class="logo">⚡ TaskFlow</div>
          <h2 style="font-size: 20px; color: #0f172a; margin-top: 8px;">Password Reset Request</h2>
        </div>
        <p>Hi <strong>{full_name}</strong>,</p>
        <p>We received a request to reset your password. Use the code below to complete your reset:</p>
        <div class="code-box">{code}</div>
        <p style="font-size: 14px; color: #64748b;">This code will expire in <strong>{settings.VERIFICATION_CODE_EXPIRE_MINUTES} minutes</strong>. If you did not request this, please ensure your account is secure.</p>
        <div class="footer">
          &copy; TaskFlow - Smart Task Manager
        </div>
      </div>
    </body>
    </html>
    """

    await send_email(to_email, subject, html_content, text_content)

