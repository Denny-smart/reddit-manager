from rest_framework import serializers
from django.utils import timezone
from .models import Post
from reddit_accounts.serializers import RedditAccountSerializer

class PostSerializer(serializers.ModelSerializer):
    reddit_account = RedditAccountSerializer(read_only=True)
    reddit_account_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    status_display = serializers.SerializerMethodField()
    can_publish = serializers.SerializerMethodField()
    can_schedule = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = [
            'id',
            'user',
            'title',
            'content', 
            'subreddit',
            'reddit_account',
            'reddit_account_id',
            'post_now',
            'scheduled_time',
            'status',
            'status_display',
            'can_publish',
            'can_schedule',
            'reddit_post_id',
            'reddit_url',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id', 
            'created_at', 
            'updated_at', 
            'reddit_post_id', 
            'reddit_url',
            'status',
            'status_display',
            'can_publish',
            'can_schedule'
        ]

    def get_status_display(self, obj):
        """Get human-readable status"""
        return obj.get_status_display()

    def get_can_publish(self, obj):
        """Check if post can be published"""
        return obj.status in [Post.STATUS_PENDING, Post.STATUS_FAILED, Post.STATUS_SCHEDULED]

    def get_can_schedule(self, obj):
        """Check if post can be scheduled"""
        return obj.status in [Post.STATUS_PENDING, Post.STATUS_FAILED]

    def validate_title(self, value):
        """Validate title length for Reddit"""
        if not value.strip():
            raise serializers.ValidationError("Title is required")
        if len(value) > 300:
            raise serializers.ValidationError(
                "Title must be 300 characters or less"
            )
        return value.strip()

    def validate_scheduled_time(self, value):
        """Validate scheduled_time is in the future"""
        if value and value <= timezone.now():
            raise serializers.ValidationError(
                "Scheduled time must be in the future"
            )
        return value

    def validate_subreddit(self, value):
        """Validate and clean subreddit name"""
        if not value:
            raise serializers.ValidationError("Subreddit is required")
        
        # Remove 'r/' prefix if present and clean
        value = value.strip().lower()
        if value.startswith('r/'):
            value = value[2:]
            
        # Basic subreddit name validation
        if not value.replace('_', '').isalnum():
            raise serializers.ValidationError(
                "Invalid subreddit name format"
            )
        return value

    def validate(self, data):
        """Validate the entire post data"""
        # Check scheduled_time requirement
        post_now = data.get('post_now', True)
        if post_now is False and not data.get('scheduled_time'):
            raise serializers.ValidationError({
                "scheduled_time": "scheduled_time is required when post_now is False"
            })
            
        # Validate content if provided
        content = data.get('content', '')
        if content and len(content) > 40000:  # Reddit's limit
            raise serializers.ValidationError({
                "content": "Content must be 40000 characters or less"
            })

        # Ensure reddit_account_id is provided when needed
        if post_now and not data.get('reddit_account_id'):
            raise serializers.ValidationError({
                "reddit_account_id": "Reddit account is required for immediate posting"
            })
        
        return data

    def create(self, validated_data):
        """Create a new post with proper status"""
        if validated_data.get('scheduled_time'):
            validated_data['status'] = Post.STATUS_SCHEDULED
            validated_data['post_now'] = False
        else:
            validated_data['status'] = Post.STATUS_PENDING
            validated_data['post_now'] = True
        
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update post with proper status changes"""
        # Handle scheduling changes
        if 'scheduled_time' in validated_data:
            if validated_data.get('scheduled_time'):
                validated_data['status'] = Post.STATUS_SCHEDULED
                validated_data['post_now'] = False
            elif instance.status == Post.STATUS_SCHEDULED:
                validated_data['status'] = Post.STATUS_PENDING
                validated_data['post_now'] = True
        
        # Reset failed status if retrying
        if instance.status == Post.STATUS_FAILED and validated_data.get('post_now'):
            validated_data['status'] = Post.STATUS_PENDING
        
        return super().update(instance, validated_data)