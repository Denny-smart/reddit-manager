from django.shortcuts import get_object_or_404
from django.utils import timezone
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
    try:
        posts = Post.objects.filter(user=request.user).order_by('-created_at')
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response(
            {'error': 'Failed to fetch posts'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def posts_posted(request):
    """List only posted/published posts"""
    try:
        posts = Post.objects.filter(
            user=request.user, 
            status=Post.STATUS_POSTED
        ).order_by('-created_at')
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response(
            {'error': 'Failed to fetch posted posts'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def posts_scheduled(request):
    """List scheduled posts for the authenticated user"""
    try:
        posts = Post.objects.filter(
            user=request.user,
            status=Post.STATUS_SCHEDULED,
            scheduled_time__gt=timezone.now()
        ).order_by('scheduled_time')
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response(
            {'error': 'Failed to fetch scheduled posts'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def posts_failed(request):
    """List failed posts for the authenticated user"""
    try:
        posts = Post.objects.filter(
            user=request.user,
            status=Post.STATUS_FAILED
        ).order_by('-created_at')
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response(
            {'error': 'Failed to fetch failed posts'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def posts_create(request):
    """Create a new post and optionally publish to Reddit"""
    try:
        serializer = PostSerializer(data=request.data, context={'request': request})
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        post = serializer.save()
        
        if post.post_now:
            reddit_account_id = request.data.get('reddit_account_id')
            
            if reddit_account_id:
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
                        'error': 'Selected Reddit account not found or inactive',
                        'post': PostSerializer(post).data
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                reddit_account = get_default_reddit_account(request.user)
                
                if not reddit_account:
                    post.status = Post.STATUS_FAILED
                    post.save()
                    return Response({
                        'error': 'No Reddit account connected. Please connect an account first.',
                        'post': PostSerializer(post).data
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            post.reddit_account = reddit_account
            post.save()
            
            success, error_message = publish_post_to_reddit(post, reddit_account)
            
            if not success:
                return Response({
                    'error': f'Post created but failed to publish: {error_message}',
                    'post': PostSerializer(post).data
                }, status=status.HTTP_207_MULTI_STATUS)
        
        return Response(PostSerializer(post).data, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        return Response(
            {'error': f'Failed to create post: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def posts_detail(request, pk):
    """Retrieve, update, or delete a specific post"""
    try:
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
    
    except Post.DoesNotExist:
        return Response(
            {'error': 'Post not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Operation failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def retry_post(request, pk):
    """Retry posting a failed post to Reddit"""
    try:
        post = get_object_or_404(Post, pk=pk, user=request.user)
        
        if post.status not in [Post.STATUS_FAILED, Post.STATUS_PENDING]:
            return Response({
                'error': 'Can only retry failed or pending posts'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        reddit_account = post.reddit_account or get_default_reddit_account(request.user)
        
        if not reddit_account:
            return Response({
                'error': 'No Reddit account available for posting'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        post.status = Post.STATUS_PENDING
        post.save()
        
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
    
    except Post.DoesNotExist:
        return Response(
            {'error': 'Post not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Retry failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def publish_post(request, pk):
    """Immediately publish a post to Reddit"""
    try:
        post = get_object_or_404(Post, pk=pk, user=request.user)
        
        if post.status == Post.STATUS_POSTED:
            return Response({
                'error': 'Post is already published'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        reddit_account = post.reddit_account or get_default_reddit_account(request.user)
        
        if not reddit_account:
            return Response({
                'error': 'No Reddit account available for posting'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        post.post_now = True
        post.scheduled_time = None
        post.status = Post.STATUS_PENDING
        post.save()
        
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
    
    except Post.DoesNotExist:
        return Response(
            {'error': 'Post not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Publishing failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def schedule_post(request, pk):
    """Schedule a post for future publication"""
    try:
        post = get_object_or_404(Post, pk=pk, user=request.user)
        
        scheduled_time = request.data.get('scheduled_time')
        if not scheduled_time:
            return Response({
                'error': 'Scheduled time is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            scheduled_time = timezone.datetime.fromisoformat(
                scheduled_time.replace('Z', '+00:00')
            )
            if scheduled_time <= timezone.now():
                return Response({
                    'error': 'Scheduled time must be in the future'
                }, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({
                'error': 'Invalid datetime format. Use ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        post.post_now = False
        post.schedule(scheduled_time)
        
        return Response({
            'message': 'Post scheduled successfully',
            'post': PostSerializer(post).data
        })
        
    except Post.DoesNotExist:
        return Response(
            {'error': 'Post not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except ValueError as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': f'Scheduling failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )