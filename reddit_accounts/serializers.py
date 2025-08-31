from rest_framework import serializers
from .models import RedditAccount

class RedditAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = RedditAccount
        fields = [
            'id',
            'reddit_username', 
            'reddit_id',
            'scopes',
            'is_active',
            'created_at',
            'updated_at'
        ]
        # Don't expose refresh_token for security
        read_only_fields = ['id', 'created_at', 'updated_at']