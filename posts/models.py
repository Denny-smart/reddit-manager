from django.db import models
from reddit_accounts.models import RedditAccount

class Post(models.Model):
    STATUS_CHOICES = (("posted", "Posted"), ("failed", "Failed"))

    reddit_account = models.ForeignKey(RedditAccount, on_delete=models.CASCADE, related_name="posts")
    title = models.CharField(max_length=300)
    content = models.TextField(blank=True, null=True)
    subreddit = models.CharField(max_length=150)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="posted")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} → r/{self.subreddit}"

