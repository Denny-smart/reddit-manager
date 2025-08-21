from django.db import models
from django.contrib.auth.models import User

class RedditAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reddit_accounts")
    reddit_username = models.CharField(max_length=150)
    refresh_token = models.TextField()  # obtained via OAuth in Week 3
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reddit_username} ({self.user.username})"

