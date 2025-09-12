# reddit_accounts/serializers.py

from rest_framework import serializers
from django.conf import settings
from .models import RedditAccount, OAuthState

class RedditAccountSerializer(serializers.ModelSerializer):
    """Serializer for Reddit account data"""
    
    # Read-only computed fields
    app_display_name = serializers.CharField(read_only=True)
    scopes_list = serializers.ListField(read_only=True)
    total_karma = serializers.SerializerMethodField()
    connection_status = serializers.SerializerMethodField()
    
    class Meta:
        model = RedditAccount
        fields = [
            'id',
            'reddit_username',
            'reddit_id',
            'app_identifier',
            'app_display_name',
            'scopes',
            'scopes_list',
            'is_active',
            'created_at',
            'updated_at',
            'karma_link',
            'karma_comment',
            'total_karma',
            'account_created',
            'has_premium',
            'connection_status',
        ]
        read_only_fields = [
            'id',
            'reddit_id',
            'created_at',
            'updated_at',
            'karma_link',
            'karma_comment',
            'account_created',
            'has_premium',
        ]
    
    def get_total_karma(self, obj):
        """Calculate total karma"""
        link_karma = obj.karma_link or 0
        comment_karma = obj.karma_comment or 0
        return link_karma + comment_karma
    
    def get_connection_status(self, obj):
        """Get connection status without making API call"""
        return {
            'is_active': obj.is_active,
            'last_updated': obj.updated_at,
            'has_refresh_token': bool(obj.refresh_token),
        }

class OAuthStateSerializer(serializers.ModelSerializer):
    """Serializer for OAuth state tracking"""
    
    class Meta:
        model = OAuthState
        fields = [
            'id',
            'state',
            'provider',
            'app_identifier',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

class RedditAppConfigSerializer(serializers.Serializer):
    """Serializer for Reddit app configuration info"""
    
    app_key = serializers.CharField()
    display_name = serializers.CharField()
    user_agent = serializers.CharField()
    is_configured = serializers.BooleanField()
    
class ConnectRedditRequestSerializer(serializers.Serializer):
    """Serializer for connect Reddit request"""
    
    app_name = serializers.CharField(default='app1')
    
    def validate_app_name(self, value):
        """Validate that the app is configured"""
        if not settings.is_reddit_app_configured(value):
            available_apps = [app[0] for app in settings.get_available_reddit_apps()]
            raise serializers.ValidationError(
                f"Reddit app '{value}' is not configured. Available apps: {available_apps}"
            )
        return value

class RedditCallbackSerializer(serializers.Serializer):
    """Serializer for Reddit OAuth callback"""
    
    code = serializers.CharField()
    state = serializers.CharField()
    app_name = serializers.CharField(required=False)  # Will be looked up from state

class SwitchAppRequestSerializer(serializers.Serializer):
    """Serializer for switching Reddit app"""
    
    new_app_name = serializers.CharField()
    
    def validate_new_app_name(self, value):
        """Validate that the new app is configured"""
        if not settings.is_reddit_app_configured(value):
            available_apps = [app[0] for app in settings.get_available_reddit_apps()]
            raise serializers.ValidationError(
                f"Reddit app '{value}' is not configured. Available apps: {available_apps}"
            )
        return value