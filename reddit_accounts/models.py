from django.conf import settings
from django.db import models

class RedditAccount(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reddit_accounts"
    )
    reddit_username = models.CharField(max_length=80)
    reddit_id = models.CharField(max_length=40, blank=True, null=True)
    refresh_token = models.CharField(max_length=512)  # from PRAW OAuth
    scopes = models.TextField(blank=True)             # comma-separated list
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"u/{self.reddit_username}"


class OAuthState(models.Model):
    """Store OAuth state for CSRF protection"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="oauth_states"
    )
    state = models.CharField(max_length=255, unique=True)
    provider = models.CharField(max_length=50)  # 'reddit', 'twitter', etc.
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'state', 'provider']),
        ]
    
    def __str__(self):
        return f"{self.provider} state for {self.user.username}"