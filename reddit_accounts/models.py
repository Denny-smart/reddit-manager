# reddit_accounts/models.py

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class RedditAccount(models.Model):
    """Model to store Reddit account connections"""
    
    # Link to Django user
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reddit_accounts')
    
    # Reddit account info
    reddit_username = models.CharField(max_length=100)
    reddit_id = models.CharField(max_length=50, blank=True, null=True)
    
    # OAuth tokens and permissions
    refresh_token = models.TextField()  # Store encrypted in production
    scopes = models.TextField(blank=True, default="")  # Comma-separated scopes
    
    # Track which Reddit app this account is connected through
    app_identifier = models.CharField(
        max_length=10, 
        default='app1',
        help_text="Which Reddit app configuration this account uses (app1, app2, etc.)"
    )
    
    # Status and metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Optional: Store additional Reddit user info
    karma_link = models.IntegerField(null=True, blank=True)
    karma_comment = models.IntegerField(null=True, blank=True)
    account_created = models.DateTimeField(null=True, blank=True)
    has_premium = models.BooleanField(default=False)
    
    class Meta:
        # Prevent duplicate connections for the same Reddit account and app
        unique_together = ['user', 'reddit_username', 'app_identifier']
        ordering = ['-created_at']
        verbose_name = 'Reddit Account'
        verbose_name_plural = 'Reddit Accounts'
    
    def __str__(self):
        app_display = settings.get_reddit_app(self.app_identifier).get('DISPLAY_NAME', self.app_identifier)
        return f"u/{self.reddit_username} ({app_display}) - {self.user.username}"
    
    @property
    def app_display_name(self):
        """Get the display name for the Reddit app"""
        return settings.get_reddit_app(self.app_identifier).get('DISPLAY_NAME', f'Reddit App {self.app_identifier}')
    
    @property
    def scopes_list(self):
        """Get scopes as a list"""
        return self.scopes.split(',') if self.scopes else []
    
    def get_reddit_instance(self):
        """Get an authenticated PRAW instance for this account"""
        import praw
        reddit_app = settings.get_reddit_app(self.app_identifier)
        
        return praw.Reddit(
            client_id=reddit_app['CLIENT_ID'],
            client_secret=reddit_app['CLIENT_SECRET'],
            redirect_uri=reddit_app['REDIRECT_URI'],
            user_agent=reddit_app['USER_AGENT'],
            refresh_token=self.refresh_token
        )
    
    def test_connection(self):
        """Test if the Reddit connection is still valid"""
        try:
            reddit = self.get_reddit_instance()
            me = reddit.user.me()
            return str(me.name) == self.reddit_username
        except:
            return False
    
    def update_user_info(self):
        """Update stored Reddit user info"""
        try:
            reddit = self.get_reddit_instance()
            me = reddit.user.me()
            
            self.karma_link = getattr(me, 'link_karma', 0)
            self.karma_comment = getattr(me, 'comment_karma', 0)
            self.has_premium = getattr(me, 'is_gold', False)
            # account_created would need datetime conversion from Reddit's timestamp
            
            self.save()
            return True
        except:
            return False


class OAuthState(models.Model):
    """Model to store OAuth state tokens for CSRF protection"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    state = models.CharField(max_length=100, unique=True)
    provider = models.CharField(max_length=20, default='reddit')
    app_identifier = models.CharField(max_length=10, default='app1')  # Which Reddit app
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        # Auto-cleanup old states
        indexes = [
            models.Index(fields=['user', 'state', 'provider']),
            models.Index(fields=['created_at']),  # For cleanup queries
        ]
    
    def __str__(self):
        return f"{self.provider} state for {self.user.username} ({self.app_identifier})"
    
    @classmethod
    def cleanup_old_states(cls, minutes=10):
        """Clean up states older than specified minutes"""
        from django.utils import timezone
        cutoff = timezone.now() - timezone.timedelta(minutes=minutes)
        return cls.objects.filter(created_at__lt=cutoff).delete()