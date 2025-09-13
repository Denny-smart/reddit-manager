from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError

User = settings.AUTH_USER_MODEL

class Post(models.Model):
    STATUS_PENDING = "pending"
    STATUS_SCHEDULED = "scheduled"
    STATUS_POSTED = "posted"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SCHEDULED, "Scheduled"),
        (STATUS_POSTED, "Posted"),
        (STATUS_FAILED, "Failed"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=300)
    content = models.TextField(blank=True, null=True, default="")  # ✅ safe
    subreddit = models.CharField(max_length=100, blank=True)
    reddit_account = models.ForeignKey(
        "reddit_accounts.RedditAccount",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Which connected Reddit account will post this"
    )
    post_now = models.BooleanField(default=True)
    scheduled_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reddit_post_id = models.CharField(max_length=64, blank=True, null=True)
    reddit_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """Validate model fields"""
        if self.post_now and self.scheduled_time:
            raise ValidationError({
                'scheduled_time': 'Cannot set scheduled time when posting now'
            })
        
        if not self.post_now and not self.scheduled_time:
            raise ValidationError({
                'scheduled_time': 'Scheduled time is required when not posting now'
            })
        
        if self.scheduled_time and self.scheduled_time <= timezone.now():
            raise ValidationError({
                'scheduled_time': 'Scheduled time must be in the future'
            })

        if len(self.title) > 300:
            raise ValidationError({
                'title': 'Title must be 300 characters or less'
            })

    def save(self, *args, **kwargs):
        """Override save to run validation"""
        self.clean()
        return super().save(*args, **kwargs)

    def schedule(self, scheduled_time):
        """Schedule a post for future publication"""
        if scheduled_time <= timezone.now():
            raise ValidationError("Scheduled time must be in the future")
        
        self.scheduled_time = scheduled_time
        self.post_now = False
        self.status = self.STATUS_SCHEDULED
        self.save()
        return self

    def publish(self):
        """Attempt to publish post to Reddit"""
        if not self.can_publish():
            raise ValidationError("Post cannot be published - missing required fields")

        try:
            # Note: Actual Reddit posting logic should be in tasks.py
            self.status = self.STATUS_POSTED
            self.post_now = True
            self.scheduled_time = None
            self.save()
            return True
        except Exception as e:
            self.mark_failed(str(e))
            raise e

    def can_publish(self):
        """Check if post meets requirements for publishing"""
        return all([
            self.title,
            self.reddit_account,
            self.subreddit,
            self.status != self.STATUS_POSTED
        ])

    def mark_failed(self, error_message=None):
        """Mark post as failed with optional error message"""
        self.status = self.STATUS_FAILED
        self.save()

    def get_status_display(self):
        """Get human-readable status"""
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

    def can_schedule(self):
        """Check if post can be scheduled"""
        return self.status in [self.STATUS_PENDING, self.STATUS_FAILED]

    def is_published(self):
        """Check if post is published"""
        return self.status == self.STATUS_POSTED

    def __str__(self):
        return f"{self.title} ({self.user})"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'scheduled_time']),
            models.Index(fields=['user', 'status']),
        ]
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'