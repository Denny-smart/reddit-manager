# posts/forms.py
from django import forms
from django.utils import timezone
from .models import Post

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "content", "subreddit", "reddit_account", "scheduled_time"]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter post title (required)",
                "maxlength": "300"
            }),
            "content": forms.Textarea(attrs={
                "class": "form-control", 
                "placeholder": "Enter post content (optional)",
                "rows": 6
            }),
            "subreddit": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g., AskReddit or r/AskReddit"
            }),
            "reddit_account": forms.Select(attrs={
                "class": "form-control"
            }),
            "scheduled_time": forms.DateTimeInput(attrs={
                "type": "datetime-local",
                "class": "form-control"
            }),
        }
        labels = {
            "title": "Post Title",
            "content": "Post Content",
            "subreddit": "Target Subreddit",
            "reddit_account": "Reddit Account",
            "scheduled_time": "Schedule For (leave empty to post now)"
        }
        help_texts = {
            "title": "Required. Maximum 300 characters.",
            "content": "Optional. The body text of your post.",
            "subreddit": "Required. Enter subreddit name (with or without 'r/' prefix).",
            "reddit_account": "Select which Reddit account to use for posting.",
            "scheduled_time": "Optional. If set, post will be scheduled for this time instead of posting immediately."
        }

    def __init__(self, *args, user=None, **kwargs):
        """
        Pass `user` from the view to limit reddit_account choices to user's active connected accounts.
        """
        super().__init__(*args, **kwargs)
        
        if user is not None:
            # Filter to only active Reddit accounts for this user
            from reddit_accounts.models import RedditAccount
            self.fields["reddit_account"].queryset = RedditAccount.objects.filter(
                user=user, 
                is_active=True
            ).order_by('-created_at')
            
            # If no active accounts, show helpful message
            if not self.fields["reddit_account"].queryset.exists():
                self.fields["reddit_account"].widget.attrs['disabled'] = True
                self.fields["reddit_account"].help_text = "No active Reddit accounts found. Please connect a Reddit account first."
        
        # Make scheduled_time optional - logic is handled by presence/absence of value
        self.fields["scheduled_time"].required = False
        self.fields["reddit_account"].required = False  # Can be set later or use default

    def clean_title(self):
        """Validate title field"""
        title = self.cleaned_data.get('title')
        if not title or not title.strip():
            raise forms.ValidationError("Title is required.")
        if len(title.strip()) > 300:
            raise forms.ValidationError("Title must be 300 characters or less.")
        return title.strip()

    def clean_subreddit(self):
        """Validate and clean subreddit name"""
        subreddit = self.cleaned_data.get('subreddit')
        if not subreddit or not subreddit.strip():
            raise forms.ValidationError("Subreddit is required.")
        
        # Clean the subreddit name
        subreddit = subreddit.strip().lower()
        if subreddit.startswith('r/'):
            subreddit = subreddit[2:]
        
        # Basic validation
        if not subreddit.replace('_', '').isalnum():
            raise forms.ValidationError("Invalid subreddit name format.")
        
        return subreddit

    def clean_scheduled_time(self):
        """Validate scheduled_time is in the future if provided"""
        scheduled_time = self.cleaned_data.get('scheduled_time')
        if scheduled_time and scheduled_time <= timezone.now():
            raise forms.ValidationError("Scheduled time must be in the future.")
        return scheduled_time

    def clean_content(self):
        """Validate content length"""
        content = self.cleaned_data.get('content', '')
        if content and len(content) > 40000:  # Reddit's limit
            raise forms.ValidationError("Content must be 40,000 characters or less.")
        return content

    def clean(self):
        """Additional form-wide validation"""
        cleaned_data = super().clean()
        user = getattr(self, '_user', None)
        reddit_account = cleaned_data.get('reddit_account')
        scheduled_time = cleaned_data.get('scheduled_time')
        
        # If no specific account chosen and no scheduled time, we need at least one active account
        if not reddit_account and not scheduled_time and user:
            from reddit_accounts.models import RedditAccount
            if not RedditAccount.objects.filter(user=user, is_active=True).exists():
                raise forms.ValidationError(
                    "No active Reddit accounts found. Please connect a Reddit account before posting."
                )
        
        return cleaned_data

    def save(self, user=None, commit=True):
        """Override save to set user and handle post_now logic"""
        instance = super().save(commit=False)
        
        if user:
            instance.user = user
            self._user = user
        
        # Set post_now based on whether scheduled_time is provided
        instance.post_now = not bool(instance.scheduled_time)
        
        # If no reddit_account specified and posting now, try to use default
        if not instance.reddit_account and instance.post_now and user:
            from reddit_accounts.models import RedditAccount
            default_account = RedditAccount.objects.filter(
                user=user, 
                is_active=True
            ).order_by('-created_at').first()
            if default_account:
                instance.reddit_account = default_account
        
        if commit:
            instance.save()
        
        return instance