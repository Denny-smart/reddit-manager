from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db.models import Index, Q

User = settings.AUTH_USER_MODEL

class Post(models.Model):
    # Status Constants
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

    # Fields with enhanced validation
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        db_index=True
    )
    title = models.CharField(
        max_length=300,
        validators=[MinLengthValidator(1)],
        help_text="Post title (required, max 300 characters)"
    )
    content = models.TextField(
        blank=True, 
        null=True, 
        default="",
        help_text="Post content (optional)"
    )
    subreddit = models.CharField(
        max_length=100,
        blank=True,
        help_text="Target subreddit name (required for posting)"
    )
    reddit_account = models.ForeignKey(
        "reddit_accounts.RedditAccount",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Which connected Reddit account will post this",
        related_name="posts"
    )
    post_now = models.BooleanField(
        default=True,
        help_text="Post immediately if True, schedule if False"
    )
    scheduled_time = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When to post (required if not posting now)",
        db_index=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True
    )
    reddit_post_id = models.CharField(
        max_length=64, 
        blank=True, 
        null=True,
        help_text="Reddit post ID after successful posting"
    )
    reddit_url = models.URLField(
        blank=True, 
        null=True,
        help_text="URL of the post on Reddit"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """Validate model fields"""
        errors = {}

        # Validate scheduling logic
        if self.post_now and self.scheduled_time:
            errors['scheduled_time'] = 'Cannot set scheduled time when posting now'
        
        if not self.post_now and not self.scheduled_time:
            errors['scheduled_time'] = 'Scheduled time is required when not posting now'
        
        if self.scheduled_time and self.scheduled_time <= timezone.now():
            errors['scheduled_time'] = 'Scheduled time must be in the future'

        # Validate required fields
        if not self.title.strip():
            errors['title'] = 'Title is required'
        elif len(self.title) > 300:
            errors['title'] = 'Title must be 300 characters or less'

        if not self.subreddit.strip():
            errors['subreddit'] = 'Subreddit is required'

        # Validate Reddit account for immediate posting
        if self.post_now and not self.reddit_account_id:
            errors['reddit_account'] = 'Reddit account is required for immediate posting'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Override save to run validation and clean data"""
        self.title = self.title.strip()
        self.subreddit = self.subreddit.strip().lower()
        if self.subreddit.startswith('r/'):
            self.subreddit = self.subreddit[2:]
            
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
            self.title.strip(),
            self.reddit_account_id,
            self.subreddit.strip(),
            self.status != self.STATUS_POSTED
        ])

    def mark_failed(self, error_message=None):
        """Mark post as failed with optional error message"""
        self.status = self.STATUS_FAILED
        self.save(update_fields=['status', 'updated_at'])

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
            models.Index(fields=['reddit_account', 'status']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'
        constraints = [
            models.CheckConstraint(
                check=Q(scheduled_time__isnull=True) | Q(scheduled_time__gt=timezone.now()),
                name='scheduled_time_future'
            )
        ]