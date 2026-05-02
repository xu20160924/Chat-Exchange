# -*- coding: utf-8 -*-
import smtplib
import ssl
from email.message import EmailMessage
from flask import current_app
from typing import Optional


def send_email(to_email: str, subject: str, body_text: str, body_html: Optional[str] = None) -> bool:
    """
    Send an email via SMTP
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body_text: Plain text body
        body_html: Optional HTML body
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        host = current_app.config.get("SMTP_HOST")
        port = current_app.config.get("SMTP_PORT")
        username = current_app.config.get("SMTP_USER")
        password = current_app.config.get("SMTP_PASSWORD")
        from_addr = current_app.config.get("SMTP_FROM")

        if not host or not username or not password:
            current_app.logger.error("SMTP settings not configured")
            return False

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to_email
        msg.set_content(body_text)
        
        # Add HTML version if provided
        if body_html:
            msg.add_alternative(body_html, subtype='html')

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host=host, port=port, context=context) as server:
            server.login(username, password)
            server.send_message(msg)
        
        return True
        
    except Exception as e:
        current_app.logger.error(f"Failed to send email to {to_email}: {e}")
        return False


def send_verification_email(to_email: str, code: str, language: str = 'en') -> bool:
    """
    Send email verification code
    
    Args:
        to_email: Recipient email address
        code: 6-digit verification code
        language: User's language preference
        
    Returns:
        bool: True if email sent successfully
    """
    from .i18n import t
    
    # Subject
    subject = t('Email Verification - Chat-Exchange', lang=language)
    
    # Plain text body
    body_text = f"""
{t('Hello', lang=language)}!

{t('Thank you for registering at Chat-Exchange', lang=language)}.

{t('Your verification code is', lang=language)}: {code}

{t('This code will expire in 10 minutes', lang=language)}.

{t('If you did not request this code, please ignore this email', lang=language)}.

{t('Best regards', lang=language)},
Chat-Exchange Team
https://chat-exchange.online
"""
    
    # HTML body
    body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #0d6efd 0%, #0b5ed7 100%);
            color: white;
            padding: 30px;
            border-radius: 10px 10px 0 0;
            text-align: center;
        }}
        .content {{
            background: #ffffff;
            padding: 30px;
            border: 1px solid #e5e5e5;
            border-top: none;
        }}
        .code-box {{
            background: #f8f9fa;
            border: 2px dashed #0d6efd;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            margin: 20px 0;
        }}
        .code {{
            font-size: 32px;
            font-weight: bold;
            color: #0d6efd;
            letter-spacing: 8px;
            font-family: 'Courier New', monospace;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 0 0 10px 10px;
            text-align: center;
            color: #666;
            font-size: 14px;
        }}
        .button {{
            display: inline-block;
            padding: 12px 30px;
            background: #0d6efd;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🌍 Chat-Exchange</h1>
        <p>{t('Email Verification', lang=language)}</p>
    </div>
    <div class="content">
        <p>{t('Hello', lang=language)}!</p>
        <p>{t('Thank you for registering at Chat-Exchange', lang=language)}.</p>
        <p>{t('Please use the verification code below to complete your registration', lang=language)}:</p>
        
        <div class="code-box">
            <div class="code">{code}</div>
        </div>
        
        <p><strong>⏰ {t('This code will expire in 10 minutes', lang=language)}.</strong></p>
        <p>{t('If you did not request this code, please ignore this email', lang=language)}.</p>
    </div>
    <div class="footer">
        <p>{t('Best regards', lang=language)},<br>
        <strong>Chat-Exchange Team</strong></p>
        <p><a href="https://chat-exchange.online" style="color: #0d6efd;">https://chat-exchange.online</a></p>
    </div>
</body>
</html>
"""
    
    return send_email(to_email, subject, body_text, body_html)


def send_welcome_email(to_email: str, name: str, language: str = 'en') -> bool:
    """
    Send welcome email after successful verification
    
    Args:
        to_email: Recipient email address
        name: User's name
        language: User's language preference
        
    Returns:
        bool: True if email sent successfully
    """
    from .i18n import t
    
    subject = t('Welcome to Chat-Exchange', lang=language)
    
    body_text = f"""
{t('Hello', lang=language)} {name}!

{t('Welcome to Chat-Exchange', lang=language)}! {t('Your account has been verified successfully', lang=language)}.

{t('You can now', lang=language)}:
- {t('Search for language partners', lang=language)}
- {t('Send and receive messages', lang=language)}
- {t('Connect with learners worldwide', lang=language)}

{t('Visit our website', lang=language)}: https://chat-exchange.online

{t('Best regards', lang=language)},
Chat-Exchange Team
"""
    
    body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #0d6efd 0%, #0b5ed7 100%);
            color: white;
            padding: 30px;
            border-radius: 10px 10px 0 0;
            text-align: center;
        }}
        .content {{
            background: #ffffff;
            padding: 30px;
            border: 1px solid #e5e5e5;
            border-top: none;
        }}
        .features {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
        }}
        .feature-item {{
            padding: 10px 0;
            border-bottom: 1px solid #e5e5e5;
        }}
        .feature-item:last-child {{
            border-bottom: none;
        }}
        .button {{
            display: inline-block;
            padding: 12px 30px;
            background: #0d6efd;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 0 0 10px 10px;
            text-align: center;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎉 {t('Welcome to Chat-Exchange', lang=language)}!</h1>
    </div>
    <div class="content">
        <p>{t('Hello', lang=language)} <strong>{name}</strong>!</p>
        <p>✅ {t('Your account has been verified successfully', lang=language)}.</p>
        
        <div class="features">
            <h3>{t('You can now', lang=language)}:</h3>
            <div class="feature-item">🔍 {t('Search for language partners', lang=language)}</div>
            <div class="feature-item">💬 {t('Send and receive messages', lang=language)}</div>
            <div class="feature-item">🌍 {t('Connect with learners worldwide', lang=language)}</div>
        </div>
        
        <center>
            <a href="https://chat-exchange.online/search" class="button">{t('Start Searching', lang=language)}</a>
        </center>
    </div>
    <div class="footer">
        <p>{t('Best regards', lang=language)},<br>
        <strong>Chat-Exchange Team</strong></p>
        <p><a href="https://chat-exchange.online" style="color: #0d6efd;">https://chat-exchange.online</a></p>
    </div>
</body>
</html>
"""
    
    return send_email(to_email, subject, body_text, body_html)
