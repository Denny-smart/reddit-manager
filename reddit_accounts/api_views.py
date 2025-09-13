import logging
import secrets
from urllib.parse import urlencode

import praw
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import RedditAccount, OAuthState
from .serializers import RedditAccountSerializer
from reddit_manager.settings import (
    is_reddit_app_configured,
    get_reddit_app,
    get_available_reddit_apps
)

# Set up logging
logger = logging.getLogger(__name__)

# Constants - Production URLs
FRONTEND_URL = "https://reddit-sync-dash.vercel.app/reddit-accounts"
ALLOWED_ORIGINS = [
    "https://reddit-sync-dash.vercel.app",
    "http://localhost:3000"  # Keep for local development
]

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reddit_apps_list(request):
    """List available Reddit apps configuration"""
    try:
        available_apps = get_available_reddit_apps()
        apps_data = []
        for app_key, display_name in available_apps:
            reddit_app = get_reddit_app(app_key)
            apps_data.append({
                'app_key': app_key,
                'display_name': display_name,
                'user_agent': reddit_app['USER_AGENT'],
                'is_configured': is_reddit_app_configured(app_key),
                'redirect_uri': reddit_app['REDIRECT_URI']
            })
        
        logger.info(f"Fetched {len(apps_data)} Reddit apps")
        return Response({
            'apps': apps_data,
            'total_apps': len(apps_data)
        })
    except Exception as e:
        logger.error(f"Error fetching Reddit apps list: {str(e)}", exc_info=True)
        return Response(
            {"error": "Failed to fetch Reddit apps configuration"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reddit_accounts_list(request):
    """List all Reddit accounts for the authenticated user"""
    try:
        accounts = RedditAccount.objects.filter(user=request.user).order_by("-created_at")
        serializer = RedditAccountSerializer(accounts, many=True)
        
        accounts_data = serializer.data
        for account_data in accounts_data:
            app_key = account_data.get('app_identifier', 'app1')
            reddit_app = get_reddit_app(app_key)
            account_data['app_display_name'] = reddit_app.get('DISPLAY_NAME', f'Reddit App {app_key}')
        
        logger.info(f"Fetched {len(accounts_data)} Reddit accounts for user: {request.user.username}")
        return Response({
            'accounts': accounts_data,
            'total_accounts': len(accounts_data)
        })
    except Exception as e:
        logger.error(f"Error fetching Reddit accounts list: {str(e)}", exc_info=True)
        return Response(
            {"error": "Failed to fetch Reddit accounts"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def reddit_callback(request):
    """Process OAuth callback code from Reddit"""
    data = request.data if request.method == 'POST' else request.query_params
    
    logger.info(f"Received callback data: {data}")
    
    if not data.get("code") or not data.get("state"):
        logger.warning("Missing code or state parameter in callback")
        return redirect(f"{FRONTEND_URL}?{urlencode({'error': 'Missing code or state parameter'})}")
    
    try:
        oauth_state = OAuthState.objects.get(
            state=data["state"],
            provider='reddit',
            created_at__gte=timezone.now() - timezone.timedelta(minutes=10)
        )
        user = oauth_state.user
        app_name = getattr(oauth_state, 'app_identifier', 'app1')
        logger.info(f"Found state for user: {user.username}, app: {app_name}")
        
    except OAuthState.DoesNotExist:
        logger.warning(f"Invalid or expired state token: {data.get('state')}")
        return redirect(f"{FRONTEND_URL}?{urlencode({'error': 'Invalid or expired state. Please try again.'})}")
    
    try:
        reddit = base_reddit(app_name)
        reddit_app = get_reddit_app(app_name)
        refresh_token = reddit.auth.authorize(data["code"])
        
        me = reddit.user.me()
        if not me:
            logger.error("Could not fetch Reddit user info after authorization")
            return redirect(f"{FRONTEND_URL}?{urlencode({'error': 'Could not fetch Reddit user info'})}")
        
        scopes_now = ",".join(sorted(reddit.auth.scopes() or []))
        logger.info(f"Got scopes for {me.name}: {scopes_now}")
        
        account, created = RedditAccount.objects.update_or_create(
            user=user,
            reddit_username=str(me.name),
            app_identifier=app_name,
            defaults={
                "reddit_id": getattr(me, "id", None),
                "refresh_token": refresh_token,
                "scopes": scopes_now,
                "is_active": True,
            },
        )
        
        logger.info(f"{'Created' if created else 'Updated'} Reddit account: {account.reddit_username}")
        oauth_state.delete()
        
        params = {
            'status': 'success',
            'username': me.name,
            'created': 'true' if created else 'false',
            'app_name': app_name
        }
        
        return redirect(f"{FRONTEND_URL}?{urlencode(params)}")
        
    except Exception as e:
        logger.error(f"Error during Reddit authentication: {str(e)}", exc_info=True)
        return redirect(f"{FRONTEND_URL}?{urlencode({'error': str(e)})}")

def get_reddit_instance(app_name='app1', refresh_token=None):
    """Get PRAW instance for a specific Reddit app"""
    if not is_reddit_app_configured(app_name):
        raise ValueError(f"Reddit app '{app_name}' is not properly configured")
    
    reddit_app = get_reddit_app(app_name)
    
    reddit_kwargs = {
        'client_id': reddit_app['CLIENT_ID'],
        'client_secret': reddit_app['CLIENT_SECRET'],
        'redirect_uri': reddit_app['REDIRECT_URI'],
        'user_agent': reddit_app['USER_AGENT'],
    }
    
    if refresh_token:
        reddit_kwargs['refresh_token'] = refresh_token
    
    return praw.Reddit(**reddit_kwargs)

def base_reddit(app_name='app1'):
    """Get PRAW instance without refresh token"""
    return get_reddit_instance(app_name)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def connect_reddit(request):
    """Generate Reddit OAuth URL"""
    app_name = request.data.get('app_name', 'app1')
    logger.info(f"Connecting Reddit account for user: {request.user.username}, app: {app_name}")
    
    if not is_reddit_app_configured(app_name):
        available_apps = [app[0] for app in get_available_reddit_apps()]
        logger.warning(f"App '{app_name}' not configured. Available: {available_apps}")
        return Response({
            "error": f"Reddit app '{app_name}' is not configured",
            "available_apps": available_apps
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        reddit = base_reddit(app_name)
        state = secrets.token_urlsafe(32)
        
        # Clean up old states
        OAuthState.objects.filter(
            user=request.user,
            created_at__lt=timezone.now() - timezone.timedelta(minutes=10)
        ).delete()
        
        # Create new state
        OAuthState.objects.create(
            user=request.user,
            state=state,
            provider='reddit',
            app_identifier=app_name
        )
        
        reddit_app = get_reddit_app(app_name)
        logger.info(f"Created state: {state} for {request.user.username}")
        
        scopes = ["identity", "read", "submit", "mysubreddits", "history"]
        auth_url = reddit.auth.url(scopes=scopes, state=state, duration="permanent")
        
        return Response({
            "auth_url": auth_url,
            "state": state,
            "app_name": app_name,
            "app_display_name": reddit_app.get('DISPLAY_NAME', f'Reddit App {app_name}'),
            "redirect_uri": reddit_app['REDIRECT_URI']
        })
        
    except Exception as e:
        logger.error(f"Error generating auth URL: {str(e)}", exc_info=True)
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_reddit_connection(request, pk):
    """Test Reddit account connection"""
    account = get_object_or_404(RedditAccount, pk=pk, user=request.user)
    logger.info(f"Testing connection for: {account.reddit_username}")
    
    try:
        reddit = get_reddit_instance(
            app_name=getattr(account, 'app_identifier', 'app1'),
            refresh_token=account.refresh_token
        )
        
        me = reddit.user.me()
        if not me:
            logger.error(f"Could not fetch info for: {account.reddit_username}")
            return Response(
                {"error": "Could not fetch Reddit user info"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        karma_info = {
            'link_karma': getattr(me, 'link_karma', 0),
            'comment_karma': getattr(me, 'comment_karma', 0),
            'total_karma': getattr(me, 'total_karma', 0),
        }
        
        return Response({
            "status": "connected",
            "reddit_username": str(me.name),
            "account_created": getattr(me, 'created_utc', None),
            "karma": karma_info,
            "has_premium": getattr(me, 'is_gold', False),
            "app_name": getattr(account, 'app_identifier', 'app1'),
            "scopes": account.scopes.split(',') if account.scopes else []
        })
        
    except Exception as e:
        logger.error(f"Connection test failed: {str(e)}", exc_info=True)
        return Response(
            {"error": f"Connection test failed: {str(e)}"}, 
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def disconnect_reddit(request, pk):
    """Disconnect Reddit account"""
    account = get_object_or_404(RedditAccount, pk=pk, user=request.user)
    username = account.reddit_username
    app_name = getattr(account, 'app_identifier', 'app1')
    reddit_app = get_reddit_app(app_name)
    
    logger.info(f"Disconnecting account: {username}")
    account.delete()
    
    return Response({
        "message": f"Successfully disconnected u/{username}"
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def switch_reddit_app(request, pk):
    """Switch Reddit app for account"""
    account = get_object_or_404(RedditAccount, pk=pk, user=request.user)
    new_app_name = request.data.get('new_app_name')
    
    if not new_app_name:
        return Response(
            {"error": "new_app_name is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    old_app_name = getattr(account, 'app_identifier', 'app1')
    logger.info(f"Switching {account.reddit_username} from {old_app_name} to {new_app_name}")
    
    if not is_reddit_app_configured(new_app_name):
        available_apps = [app[0] for app in get_available_reddit_apps()]
        return Response({
            "error": f"Reddit app '{new_app_name}' is not configured",
            "available_apps": available_apps
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if old_app_name == new_app_name:
        return Response(
            {"error": f"Account is already using {new_app_name}"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    account.app_identifier = new_app_name
    account.save()
    
    old_app = get_reddit_app(old_app_name)
    new_app = get_reddit_app(new_app_name)
    
    return Response({
        "message": f"Successfully switched u/{account.reddit_username}",
        "old_app": old_app_name,
        "new_app": new_app_name,
        "account": RedditAccountSerializer(account).data
    })