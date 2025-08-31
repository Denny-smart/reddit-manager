# posts/api_views.py
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Post
from .serializers import PostSerializer
from .utils import publish_post_to_reddit, get_default_reddit_account
from reddit_accounts.models import RedditAccount

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def posts_list(request):
    """List all posts for the authenticated user"""
    posts = Post.objects.filter(user=request.user).order_by('-created_at')
    serializer = PostSerializer(posts, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def posts_create(request):
    """Create a new post and optionally publish to Reddit"""
    serializer = PostSerializer(data=request.data, context={'request': request})
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Save the post first
    post = serializer.save()
    
    # Handle Reddit posting
    if post.post_now:
        # Get Reddit account to use
        reddit_account_id = request.data.get('reddit_account_id')
        
        if reddit_account_id:
            # Use specified Reddit account
            try:
                reddit_account = RedditAccount.objects.get(
                    id=reddit_account_id, 
                    user=request.user, 
                    is_active=True
                )
            except RedditAccount.DoesNotExist:
                post.status = Post.STATUS_FAILED
                post.save()
                return Response({
                    'error': 'Selected Reddit account not found or inactive'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Use default (most recent) Reddit account
            reddit_account = get_default_reddit_account(request.user)
            
            if not reddit_account:
                post.status = Post.STATUS_FAILED
                post.save()
                return Response({
                    'error': 'No Reddit account connected. Please connect a Reddit account first.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set the Reddit account for the post
        post.reddit_account = reddit_account
        post.save()
        
        # Attempt to publish to Reddit
        success, error_message = publish_post_to_reddit(post, reddit_account)
        
        if not success:
            return Response({
                'error': f'Post created but failed to publish to Reddit: {error_message}',
                'post': PostSerializer(post).data
            }, status=status.HTTP_207_MULTI_STATUS)  # 207 = partial success
    
    # Return the created post
    return Response(PostSerializer(post).data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def posts_posted(request):
    """List only posted/published posts"""
    posts = Post.objects.filter(
        user=request.user, 
        status=Post.STATUS_POSTED
    ).order_by('-created_at')
    
    serializer = PostSerializer(posts, many=True)
    return Response(serializer.data)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def posts_detail(request, pk):
    """Retrieve, update, or delete a specific post"""
    post = get_object_or_404(Post, pk=pk, user=request.user)
    
    if request.method == 'GET':
        serializer = PostSerializer(post)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = PostSerializer(post, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        title = post.title
        post.delete()
        return Response({
            "message": f"Successfully deleted post '{title}'"
        })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def retry_post(request, pk):
    """Retry posting a failed post to Reddit"""
    post = get_object_or_404(Post, pk=pk, user=request.user)
    
    if post.status not in [Post.STATUS_FAILED, Post.STATUS_DRAFT]:
        return Response({
            'error': 'Can only retry failed or draft posts'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get Reddit account
    reddit_account = post.reddit_account or get_default_reddit_account(request.user)
    
    if not reddit_account:
        return Response({
            'error': 'No Reddit account available for posting'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Reset status to pending before attempting
    post.status = Post.STATUS_PENDING
    post.save()
    
    # Attempt to publish
    success, error_message = publish_post_to_reddit(post, reddit_account)
    
    if success:
        return Response({
            'message': 'Post successfully published to Reddit',
            'post': PostSerializer(post).data
        })
    else:
        return Response({
            'error': f'Failed to publish to Reddit: {error_message}',
            'post': PostSerializer(post).data
        }, status=status.HTTP_400_BAD_REQUEST)