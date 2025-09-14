# posts/serializers.py
from rest_framework import serializers
from django.utils import timezone
from .models import Post
from reddit_accounts.serializers import RedditAccountSerializer
from reddit_accounts.models import RedditAccount

class PostSerializer(serializers.ModelSerializer):
    reddit_account = RedditAccountSerializer(read_only=True)
    reddit_account_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    status_display = serializers.SerializerMethodField()
    can_publish = serializers.SerializerMethodField()
    can_schedule = serializers.SerializerMethodField()
    available_reddit_accounts = serializers.SerializerMethodField()
    
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
            'available_reddit_accounts',
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
            'can_schedule',
            'available_reddit_accounts'
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

    def get_available_reddit_accounts(self, obj):
        """Get available Reddit accounts for this user"""
        accounts = obj.get_available_reddit_accounts()
        return RedditAccountSerializer(accounts, many=True).data

    def validate_title(self, value):
        """Validate title length for Reddit"""
        if not value or not value.strip():
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
        if not value or not value.strip():
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

    def validate_reddit_account_id(self, value):
        """Validate that the Reddit account belongs to the user and is active"""
        if value is not None:
            user = self.context['request'].user
            try:
                reddit_account = RedditAccount.objects.get(
                    id=value,
                    user=user,
                    is_active=True
                )
                return value
            except RedditAccount.DoesNotExist:
                raise serializers.ValidationError(
                    "Selected Reddit account not found or inactive"
                )
        return value

    def validate(self, data):
        """Validate the entire post data"""
        user = self.context['request'].user
        post_now = data.get('post_now', True)
        reddit_account_id = data.get('reddit_account_id')
        
        # Check scheduled_time requirement
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

        # For immediate posting, ensure user has at least one Reddit account
        if post_now:
            # Check if user has any active Reddit accounts
            user_accounts = RedditAccount.objects.filter(user=user, is_active=True)
            
            if not user_accounts.exists():
                raise serializers.ValidationError({
                    "reddit_account_id": "No Reddit accounts connected. Please connect a Reddit account first."
                })
            
            # If no specific account chosen, we'll use default in create method
            # If specific account chosen, it's already validated above
        
        return data

    def create(self, validated_data):
        """Create a new post with proper Reddit account handling"""
        user = self.context['request'].user
        reddit_account_id = validated_data.get('reddit_account_id')
        post_now = validated_data.get('post_now', True)
        
        # Handle Reddit account assignment
        if post_now:
            if reddit_account_id:
                # Use the specified account (already validated)
                try:
                    reddit_account = RedditAccount.objects.get(
                        id=reddit_account_id,
                        user=user,
                        is_active=True
                    )
                    validated_data['reddit_account'] = reddit_account
                except RedditAccount.DoesNotExist:
                    # This shouldn't happen due to validation, but just in case
                    pass
            else:
                # Use default account (most recent active one)
                default_account = RedditAccount.objects.filter(
                    user=user,
                    is_active=True
                ).order_by('-created_at').first()
                
                if default_account:
                    validated_data['reddit_account'] = default_account
        
        # Remove reddit_account_id from validated_data as it's not a model field
        validated_data.pop('reddit_account_id', None)
        
        # Set status based on scheduling
        if validated_data.get('scheduled_time'):
            validated_data['status'] = Post.STATUS_SCHEDULED
            validated_data['post_now'] = False
        else:
            validated_data['status'] = Post.STATUS_PENDING
            validated_data['post_now'] = True
        
        # Create the post with skip_clean to avoid model validation issues during creation
        post = Post(**validated_data)
        post.save(skip_clean=True)
        
        return post

    def update(self, instance, validated_data):
        """Update post with proper status changes and Reddit account handling"""
        user = self.context['request'].user
        reddit_account_id = validated_data.get('reddit_account_id')
        
        # Handle Reddit account updates
        if reddit_account_id:
            try:
                reddit_account = RedditAccount.objects.get(
                    id=reddit_account_id,
                    user=user,
                    is_active=True
                )
                validated_data['reddit_account'] = reddit_account
            except RedditAccount.DoesNotExist:
                # This shouldn't happen due to validation, but just in case
                pass
        
        # Remove reddit_account_id from validated_data
        validated_data.pop('reddit_account_id', None)
        
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
        
        # Update the instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save(skip_clean=True)
        return instance