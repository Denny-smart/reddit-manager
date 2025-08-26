from django.db import models
from django.conf import settings

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

    def __str__(self):
        return f"{self.title} ({self.user})"
