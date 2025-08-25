from django.db import models
from django.contrib.auth.models import User

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # allow null for now
    title = models.CharField(max_length=255)
    content = models.TextField(null=True, blank=True)
    subreddit = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title
