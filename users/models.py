from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
import secrets
import string

class Profile(models.Model):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('POSTER', 'Poster'),
        ('VIEWER', 'Viewer'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='VIEWER')
    google_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    profile_picture = models.URLField(blank=True, null=True)
    
    # Email verification fields
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=32, blank=True, null=True)
    verification_token_created = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"
    
    def generate_verification_token(self):
        """Generate a new email verification token."""
        self.email_verification_token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        self.verification_token_created = timezone.now()
        self.save()
        return self.email_verification_token
    
    def is_verification_token_valid(self):
        """Check if verification token is still valid (24 hours)."""
        if not self.verification_token_created:
            return False
        expiry = self.verification_token_created + timedelta(hours=24)
        return timezone.now() < expiry

class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=32, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)
    
    def is_valid(self):
        """Check if token is still valid (not expired and not used)."""
        expiry_time = self.created_at + timedelta(seconds=3600)  # 1 hour
        return not self.used and timezone.now() < expiry_time
    
    def __str__(self):
        return f"Reset token for {self.user.username}"

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.is_superuser:
            Profile.objects.create(user=instance, role='ADMIN', email_verified=True)  # Admins auto-verified
        else:
            profile = Profile.objects.create(user=instance, role='VIEWER')
            profile.generate_verification_token()  # Generate token for new users
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()