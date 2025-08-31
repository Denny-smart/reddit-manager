from rest_framework import serializers
from .models import Post
from reddit_accounts.serializers import RedditAccountSerializer

class PostSerializer(serializers.ModelSerializer):
    reddit_account = RedditAccountSerializer(read_only=True)
    reddit_account_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    
    class Meta:
        model = Post
        fields = [
            'id',
            'user',  # Add this field
            'title',
            'content', 
            'subreddit',
            'reddit_account',
            'reddit_account_id',
            'post_now',
            'scheduled_time',
            'status',
            'reddit_post_id',
            'reddit_url',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'reddit_post_id', 'reddit_url']

    def validate(self, data):
        # If post_now is explicitly False, scheduled_time is required
        # But if post_now is True or not provided, no scheduled_time needed
        post_now = data.get('post_now', True)  # Default to True if not provided
        
        if post_now is False and not data.get('scheduled_time'):
            raise serializers.ValidationError(
                "scheduled_time is required when post_now is False"
            )
        return data