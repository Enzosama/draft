import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.config import settings
from typing import Optional

async def send_email(
    to_email: str, 
    subject: str, 
    body: str,
    from_email: Optional[str] = None
) -> bool:
    """
    Send email via SMTP
    
    Args:
        to_email: Recipient email
        subject: Email subject
        body: HTML body
        from_email: Sender email (uses SMTP_FROM if None)
    
    Returns:
        True if sent successfully
    """
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print("⚠️ Email not configured - skipping send")
        return False
    
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = from_email or settings.SMTP_FROM
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Attach HTML body
        html_part = MIMEText(body, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ Email sent to: {to_email}")
        return True
    
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False

async def send_password_reset_email(email: str, reset_token: str) -> bool:
    """Send password reset email with token"""
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    
    subject = f"🔐 Password Reset - {settings.APP_NAME}"
    
    body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #4F46E5; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 5px 5px; }}
            .button {{ display: inline-block; padding: 12px 30px; background: #4F46E5; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 Password Reset Request</h1>
            </div>
            <div class="content">
                <p>Hello,</p>
                <p>You requested to reset your password for <strong>{settings.APP_NAME}</strong>.</p>
                <p>Click the button below to reset your password:</p>
                <a href="{reset_url}" class="button">Reset Password</a>
                <p>Or copy this link: <br><code>{reset_url}</code></p>
                <p><strong>⏰ This link will expire in 1 hour.</strong></p>
                <p>If you didn't request this, please ignore this email.</p>
            </div>
            <div class="footer">
                <p>&copy; {settings.APP_NAME} - Automated email, please do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return await send_email(email, subject, body)

async def send_welcome_email(email: str, fullname: str) -> bool:
    """Send welcome email after registration"""
    subject = f"🎉 Welcome to {settings.APP_NAME}!"
    
    body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #10B981; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 5px 5px; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎉 Welcome to {settings.APP_NAME}!</h1>
            </div>
            <div class="content">
                <p>Hi <strong>{fullname}</strong>,</p>
                <p>Thank you for registering with {settings.APP_NAME}!</p>
                <p>You can now access all features of our platform.</p>
                <p>If you have any questions, feel free to contact our support team.</p>
            </div>
            <div class="footer">
                <p>&copy; {settings.APP_NAME}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return await send_email(email, subject, body)
