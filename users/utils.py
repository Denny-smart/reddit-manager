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

def send_password_reset_email(user, reset_token, frontend_url='https://reddit-sync-dash.vercel.app'):
    """
    Send password reset email to user.
    
    Args:
        user: User instance
        reset_token: Password reset token
        frontend_url: Frontend URL for reset link
    """
    reset_link = f"{frontend_url}/reset-password?token={reset_token}"
    
    subject = 'Reset Your Password - Reddit Manager'
    
    # Create HTML email content
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #333;">Reset Your Password</h2>
        <p>Hi {user.username},</p>
        <p>You requested a password reset for your Reddit Manager account.</p>
        <p>Click the button below to reset your password:</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_link}" style="background-color: #dc3545; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">Reset Password</a>
        </div>
        <p>If the button doesn't work, copy and paste this link in your browser:</p>
        <p style="word-break: break-all; color: #666;">{reset_link}</p>
        <p style="color: #888; font-size: 12px;">This link will expire in 1 hour.</p>
        <p style="color: #888; font-size: 12px;">If you didn't request this reset, please ignore this email.</p>
        <br>
        <p>Best regards,<br>Reddit Manager Team</p>
    </body>
    </html>
    """
    
    # Plain text version
    plain_message = f"""
    Reset Your Password
    
    Hi {user.username},
    
    You requested a password reset for your Reddit Manager account.
    
    Click this link to reset your password: {reset_link}
    
    This link will expire in 1 hour.
    
    If you didn't request this reset, please ignore this email.
    
    Best regards,
    Reddit Manager Team
    """
    
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

def send_verification_email(user, verification_token, frontend_url='https://reddit-sync-dash.vercel.app'):
    """
    Send email verification email to user.
    
    Args:
        user: User instance
        verification_token: Email verification token
        frontend_url: Frontend URL for verification link
    """
    verification_link = f"{frontend_url}/verify-email?token={verification_token}"
    
    subject = 'Verify Your Email - Reddit Manager'
    
    # Create HTML email content
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #333;">Verify Your Email Address</h2>
        <p>Hi {user.username},</p>
        <p>Thank you for signing up for Reddit Manager! Please verify your email address to complete your registration.</p>
        <p>Click the button below to verify your email:</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{verification_link}" style="background-color: #28a745; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">Verify Email Address</a>
        </div>
        <p>If the button doesn't work, copy and paste this link in your browser:</p>
        <p style="word-break: break-all; color: #666;">{verification_link}</p>
        <p style="color: #888; font-size: 12px;">This verification link will expire in 10 minutes.</p>
        <p style="color: #888; font-size: 12px;">If you didn't create this account, please ignore this email.</p>
        <br>
        <p>Welcome to Reddit Manager!<br>The Reddit Manager Team</p>
    </body>
    </html>
    """
    
    # Plain text version
    plain_message = f"""
    Verify Your Email Address
    
    Hi {user.username},
    
    Thank you for signing up for Reddit Manager! Please verify your email address to complete your registration.
    
    Click this link to verify your email: {verification_link}
    
    This verification link will expire in 10 minutes.
    
    If you didn't create this account, please ignore this email.
    
    Welcome to Reddit Manager!
    The Reddit Manager Team
    """
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Verification email sent to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
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
        # Check for Google Client ID (use the updated setting name)
        google_client_id = getattr(settings, 'GOOGLE_CLIENT_ID', None) or getattr(settings, 'GOOGLE_OAUTH2_CLIENT_ID', None)
        
        if not google_client_id:
            logger.error("Google OAuth not configured - missing GOOGLE_CLIENT_ID")
            return None
            
        idinfo = id_token.verify_oauth2_token(
            token, 
            requests.Request(), 
            google_client_id
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
