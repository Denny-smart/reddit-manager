# posts/forms.py
from django import forms
from .models import Post
from django.utils import timezone

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "content", "subreddit", "reddit_account", "post_now", "scheduled_time"]
        widgets = {
            "scheduled_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        """
        Pass `user` from the view to limit reddit_account choices to user's connected accounts.
        """
        super().__init__(*args, **kwargs)
        if user is not None:
            # adjust this queryset to match your reddit_accounts model field name for relation to user
            self.fields["reddit_account"].queryset = (
                self.fields["reddit_account"].queryset.filter(user=user)
            )
        # hide scheduled_time unless post_now is False (optional client-side JS)
