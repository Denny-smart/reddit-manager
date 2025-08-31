import secrets
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import praw
from .models import RedditAccount, OAuthState  # You'll need to create OAuthState model
from .serializers import RedditAccountSerializer

def base_reddit():
    """PRAW instance without refresh_token (for generating auth URLs and exchanging code)"""
    return praw.Reddit(
        client_id=settings.REDDIT_CLIENT_ID,
        client_secret=settings.REDDIT_CLIENT_SECRET,
        redirect_uri=settings.REDDIT_REDIRECT_URI,
        user_agent=settings.REDDIT_USER_AGENT,
    )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reddit_accounts_list(request):
    """List all Reddit accounts for the authenticated user"""
    accounts = RedditAccount.objects.filter(user=request.user).order_by("-created_at")
    serializer = RedditAccountSerializer(accounts, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def connect_reddit(request):
    """Generate Reddit OAuth URL for frontend to redirect to"""
    reddit = base_reddit()
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
        provider='reddit'
    )
    
    print(f"Generated state: {state}")
    print(f"Stored state in database for user: {request.user.username}")
    
    # Choose scopes you need
    scopes = ["identity", "read", "submit", "mysubreddits", "history"]
    
    # Generate auth URL
    auth_url = reddit.auth.url(scopes=scopes, state=state, duration="permanent")
    
    return Response({
        "auth_url": auth_url,
        "state": state
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reddit_callback(request):
    """Process OAuth callback code from Reddit"""
    data = request.data
    
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
    except OAuthState.DoesNotExist:
        print(f"State validation failed! No matching state found in database.")
        print(f"Looking for state: {data['state']} for user: {request.user.username}")
        return Response(
            {"error": "State mismatch. Please try again."}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    reddit = base_reddit()
    
    try:
        # Exchange code for refresh_token
        refresh_token = reddit.auth.authorize(data["code"])
        print(f"Successfully got refresh token: {refresh_token[:10]}...")
    except Exception as e:
        print(f"Authorization failed: {str(e)}")
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
        
        print(f"Successfully fetched Reddit user: {me.name}")
        
        # Get current scopes
        scopes_now = ",".join(sorted(reddit.auth.scopes() or []))
        
        # Save or update the linked account
        account, created = RedditAccount.objects.update_or_create(
            user=request.user,
            reddit_username=str(me.name),
            defaults={
                "reddit_id": getattr(me, "id", None),
                "refresh_token": refresh_token,
                "scopes": scopes_now,
                "is_active": True,
            },
        )
        
        print(f"Account {'created' if created else 'updated'}: {account.reddit_username}")
        
        # Clean up the used state
        oauth_state.delete()
        
        serializer = RedditAccountSerializer(account)
        return Response({
            "message": f"Successfully connected Reddit account u/{me.name}",
            "account": serializer.data,
            "created": created
        })
        
    except Exception as e:
        print(f"Failed to save Reddit account: {str(e)}")
        return Response(
            {"error": f"Failed to save Reddit account: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def disconnect_reddit(request, pk):
    """Disconnect a specific Reddit account"""
    account = get_object_or_404(RedditAccount, pk=pk, user=request.user)
    username = account.reddit_username
    account.delete()
    
    return Response({
        "message": f"Successfully disconnected Reddit account u/{username}"
    })