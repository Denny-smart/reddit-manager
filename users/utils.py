import secrets
import string
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.models import User
from google.auth.transport import requests
from google.oauth2 import id_token
import logging

logger = logging.getLogger(__name__)

def generate_reset_token():
    """Generate a secure random token for password reset."""
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

def send_password_reset_email(user, reset_token, frontend_url='https://reddit-sync-dash.vercel.app/'):
    """
    Send password reset email to user.
    
    Args:
        user: User instance
        reset_token: Password reset token
        frontend_url: Frontend URL for reset link
    """
    reset_link = f"{frontend_url}/reset-password?token={reset_token}&email={user.email}"
    
    subject = 'Reset Your Password - Reddit Manager'
    
    # Create HTML email content
    html_message = f"""
    <html>
    <body>
        <h2>Password Reset Request</h2>
        <p>Hi {user.username},</p>
        <p>You requested a password reset for your Reddit Manager account.</p>
        <p>Click the link below to reset your password:</p>
        <p><a href="{reset_link}" style="background-color: #007bff; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
        <p>If the button doesn't work, copy and paste this link in your browser:</p>
        <p>{reset_link}</p>
        <p>This link will expire in 1 hour.</p>
        <p>If you didn't request this reset, please ignore this email.</p>
        <br>
        <p>Best regards,<br>Reddit Manager Team</p>
    </body>
    </html>
    """
    
    # Plain text version
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Password reset email sent to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
        return False

def verify_google_token(token):
    """
    Verify Google OAuth token and return user info.
    
    Args:
        token: Google ID token
        
    Returns:
        dict: User info from Google or None if invalid
    """
    try:
        idinfo = id_token.verify_oauth2_token(
            token, 
            requests.Request(), 
            settings.GOOGLE_OAUTH2_CLIENT_ID
        )
        
        # Verify the issuer
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
            
        return {
            'google_id': idinfo['sub'],
            'email': idinfo['email'],
            'first_name': idinfo.get('given_name', ''),
            'last_name': idinfo.get('family_name', ''),
            'name': idinfo.get('name', ''),
            'picture': idinfo.get('picture', ''),
            'email_verified': idinfo.get('email_verified', False)
        }
    except ValueError as e:
        logger.error(f"Invalid Google token: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error verifying Google token: {str(e)}")
        return None

def generate_username_from_email(email):
    """Generate a unique username from email."""
    base_username = email.split('@')[0]
    username = base_username
    counter = 1
    
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1
        
    return username