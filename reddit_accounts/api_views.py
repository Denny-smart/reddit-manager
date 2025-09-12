import secrets
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import praw
from .models import RedditAccount, OAuthState
from .serializers import RedditAccountSerializer

# Import the helper functions from settings
from reddit_manager.settings import (
    is_reddit_app_configured,
    get_reddit_app,
    get_available_reddit_apps
)

def get_reddit_instance(app_name='app1', refresh_token=None):
    """
    Get PRAW instance for a specific Reddit app
    
    Args:
        app_name (str): The Reddit app to use ('app1', 'app2', etc.)
        refresh_token (str, optional): If provided, creates authenticated instance
    
    Returns:
        praw.Reddit: Configured Reddit instance
    """
    # Get Reddit app configuration
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
    """
    PRAW instance without refresh_token (for generating auth URLs and exchanging code)
    
    Args:
        app_name (str): The Reddit app to use
    """
    return get_reddit_instance(app_name)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reddit_apps_list(request):
    """List all available Reddit apps for connection"""
    available_apps = get_available_reddit_apps()
    
    apps_data = []
    for app_key, display_name in available_apps:
        reddit_app = get_reddit_app(app_key)
        apps_data.append({
            'app_key': app_key,
            'display_name': display_name,
            'user_agent': reddit_app['USER_AGENT'],
            'is_configured': is_reddit_app_configured(app_key),
            'redirect_uri': reddit_app['REDIRECT_URI']  # Added for debugging
        })
    
    return Response({
        'available_apps': apps_data,
        'total_apps': len(apps_data)
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reddit_accounts_list(request):
    """List all Reddit accounts for the authenticated user"""
    accounts = RedditAccount.objects.filter(user=request.user).order_by("-created_at")
    serializer = RedditAccountSerializer(accounts, many=True)
    
    # Add app display names to the response
    accounts_data = serializer.data
    for account_data in accounts_data:
        app_key = account_data.get('app_identifier', 'app1')
        reddit_app = get_reddit_app(app_key)
        account_data['app_display_name'] = reddit_app.get('DISPLAY_NAME', f'Reddit App {app_key}')
    
    return Response({
        'accounts': accounts_data,
        'total_accounts': len(accounts_data)
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def connect_reddit(request):
    """
    Generate Reddit OAuth URL for frontend to redirect to
    
    Expected POST data:
    {
        "app_name": "app1"  # or "app2", etc. (optional, defaults to "app1")
    }
    """
    # Get app name from request, default to 'app1'
    app_name = request.data.get('app_name', 'app1')
    
    # Validate app exists and is configured
    if not is_reddit_app_configured(app_name):
        available_apps = [app[0] for app in get_available_reddit_apps()]
        return Response({
            "error": f"Reddit app '{app_name}' is not configured",
            "available_apps": available_apps
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        reddit = base_reddit(app_name)
    except ValueError as e:
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    state = secrets.token_urlsafe(32)
    
    # Store state in database instead of session
    # Clean up old states for this user (older than 10 minutes)
    OAuthState.objects.filter(
        user=request.user,
        created_at__lt=timezone.now() - timezone.timedelta(minutes=10)
    ).delete()
    
    # Create new state record
    OAuthState.objects.create(
        user=request.user,
        state=state,
        provider='reddit',
        app_identifier=app_name  # Store which app this state is for
    )
    
    reddit_app = get_reddit_app(app_name)
    
    print(f"Generated state: {state} for app: {app_name}")
    print(f"Using redirect URI: {reddit_app['REDIRECT_URI']}")
    print(f"Stored state in database for user: {request.user.username}")
    
    # Choose scopes you need
    scopes = ["identity", "read", "submit", "mysubreddits", "history"]
    
    # Generate auth URL - PRAW will use the redirect_uri from the reddit instance
    auth_url = reddit.auth.url(scopes=scopes, state=state, duration="permanent")
    
    # Log the generated auth URL for debugging
    print(f"Generated auth URL: {auth_url}")
    
    return Response({
        "auth_url": auth_url,
        "state": state,
        "app_name": app_name,
        "app_display_name": reddit_app.get('DISPLAY_NAME', f'Reddit App {app_name}'),
        "redirect_uri": reddit_app['REDIRECT_URI']  # Include for debugging
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reddit_callback(request):
    """
    Process OAuth callback code from Reddit
    
    Expected POST data:
    {
        "code": "oauth_code_from_reddit",
        "state": "state_token",
        "app_name": "app1"  # optional, will be looked up from state
    }
    """
    data = request.data
    
    print(f"Received callback data: {data}")
    print(f"Received state: {data.get('state')}")
    print(f"Current user: {request.user.username}")
    
    # Validate required fields
    if not data.get("code") or not data.get("state"):
        return Response(
            {"error": "Missing code or state parameter"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate state using database storage
    try:
        oauth_state = OAuthState.objects.get(
            user=request.user,
            state=data["state"],
            provider='reddit',
            created_at__gte=timezone.now() - timezone.timedelta(minutes=10)  # 10 minute expiry
        )
        print(f"Found matching state in database: {oauth_state.state}")
        
        # Get the app name from the state record
        app_name = getattr(oauth_state, 'app_identifier', 'app1')
        print(f"Using app: {app_name}")
        
    except OAuthState.DoesNotExist:
        print(f"State validation failed! No matching state found in database.")
        print(f"Looking for state: {data['state']} for user: {request.user.username}")
        
        # List all states for this user for debugging
        user_states = OAuthState.objects.filter(user=request.user, provider='reddit')
        print(f"User has {user_states.count()} Reddit states:")
        for state_obj in user_states:
            print(f"  - State: {state_obj.state}, Age: {timezone.now() - state_obj.created_at}")
        
        return Response(
            {"error": "State mismatch. Please try again."}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        reddit = base_reddit(app_name)
        reddit_app = get_reddit_app(app_name)
        print(f"Using redirect URI for callback: {reddit_app['REDIRECT_URI']}")
    except ValueError as e:
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Exchange code for refresh_token
        refresh_token = reddit.auth.authorize(data["code"])
        print(f"Successfully got refresh token for {app_name}: {refresh_token[:10] if refresh_token else 'None'}...")
    except Exception as e:
        print(f"Authorization failed for {app_name}: {str(e)}")
        return Response(
            {"error": f"Authorization failed: {str(e)}"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Use the now-authorized instance to fetch Reddit user
        me = reddit.user.me()
        if not me:
            return Response(
                {"error": "Could not fetch Reddit user after auth"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        print(f"Successfully fetched Reddit user: {me.name} via {app_name}")
        
        # Get current scopes
        scopes_now = ",".join(sorted(reddit.auth.scopes() or []))
        
        # Save or update the linked account
        account, created = RedditAccount.objects.update_or_create(
            user=request.user,
            reddit_username=str(me.name),
            app_identifier=app_name,  # Track which app this account is connected through
            defaults={
                "reddit_id": getattr(me, "id", None),
                "refresh_token": refresh_token,
                "scopes": scopes_now,
                "is_active": True,
            },
        )
        
        print(f"Account {'created' if created else 'updated'}: {account.reddit_username} via {app_name}")
        
        # Clean up the used state
        oauth_state.delete()
        
        serializer = RedditAccountSerializer(account)
        reddit_app = get_reddit_app(app_name)
        
        return Response({
            "message": f"Successfully connected Reddit account u/{me.name} via {reddit_app.get('DISPLAY_NAME', app_name)}",
            "account": serializer.data,
            "created": created,
            "app_name": app_name,
            "app_display_name": reddit_app.get('DISPLAY_NAME', f'Reddit App {app_name}')
        })
        
    except Exception as e:
        print(f"Failed to save Reddit account: {str(e)}")
        return Response(
            {"error": f"Failed to save Reddit account: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_reddit_connection(request, pk):
    """Test a Reddit account connection and fetch basic info"""
    account = get_object_or_404(RedditAccount, pk=pk, user=request.user)
    
    try:
        # Get authenticated Reddit instance for this account
        reddit = get_reddit_instance(
            app_name=getattr(account, 'app_identifier', 'app1'),
            refresh_token=account.refresh_token
        )
        
        # Test the connection
        me = reddit.user.me()
        if not me:
            return Response(
                {"error": "Could not fetch Reddit user info"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get some basic stats
        try:
            karma_info = {
                'link_karma': getattr(me, 'link_karma', 0),
                'comment_karma': getattr(me, 'comment_karma', 0),
                'total_karma': getattr(me, 'total_karma', 0),
            }
        except:
            karma_info = {'error': 'Could not fetch karma info'}
        
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
        print(f"Reddit connection test failed: {str(e)}")
        return Response(
            {"error": f"Connection test failed: {str(e)}"}, 
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def disconnect_reddit(request, pk):
    """Disconnect a specific Reddit account"""
    account = get_object_or_404(RedditAccount, pk=pk, user=request.user)
    username = account.reddit_username
    app_name = getattr(account, 'app_identifier', 'app1')
    reddit_app = get_reddit_app(app_name)
    
    account.delete()
    
    return Response({
        "message": f"Successfully disconnected Reddit account u/{username} from {reddit_app.get('DISPLAY_NAME', app_name)}"
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def switch_reddit_app(request, pk):
    """
    Switch a Reddit account to use a different Reddit app
    
    Expected POST data:
    {
        "new_app_name": "app2"
    }
    """
    account = get_object_or_404(RedditAccount, pk=pk, user=request.user)
    new_app_name = request.data.get('new_app_name')
    
    if not new_app_name:
        return Response(
            {"error": "new_app_name is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not is_reddit_app_configured(new_app_name):
        available_apps = [app[0] for app in get_available_reddit_apps()]
        return Response({
            "error": f"Reddit app '{new_app_name}' is not configured",
            "available_apps": available_apps
        }, status=status.HTTP_400_BAD_REQUEST)
    
    old_app_name = getattr(account, 'app_identifier', 'app1')
    if old_app_name == new_app_name:
        return Response(
            {"error": f"Account is already using {new_app_name}"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Update the account to use the new app
    account.app_identifier = new_app_name
    account.save()
    
    old_app = get_reddit_app(old_app_name)
    new_app = get_reddit_app(new_app_name)
    
    return Response({
        "message": f"Successfully switched u/{account.reddit_username} from {old_app.get('DISPLAY_NAME', old_app_name)} to {new_app.get('DISPLAY_NAME', new_app_name)}",
        "old_app": old_app_name,
        "new_app": new_app_name,
        "account": RedditAccountSerializer(account).data
    })