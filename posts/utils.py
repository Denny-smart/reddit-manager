# posts/reddit_utils.py
import praw
from django.conf import settings
from reddit_accounts.models import RedditAccount
from .models import Post

def get_authenticated_reddit(reddit_account: RedditAccount):
    """Create an authenticated PRAW instance using stored refresh_token"""
    try:
        reddit = praw.Reddit(
            client_id=settings.REDDIT_CLIENT_ID,
            client_secret=settings.REDDIT_CLIENT_SECRET,
            refresh_token=reddit_account.refresh_token,
            user_agent=settings.REDDIT_USER_AGENT,
        )
        
        # Test the connection
        reddit.user.me()
        return reddit
    except Exception as e:
        print(f"Failed to authenticate Reddit for {reddit_account.reddit_username}: {e}")
        return None

def publish_post_to_reddit(post: Post, reddit_account: RedditAccount):
    """
    Actually publish a post to Reddit and update the post record
    Returns: (success: bool, error_message: str)
    """
    try:
        # Get authenticated Reddit instance
        reddit = get_authenticated_reddit(reddit_account)
        if not reddit:
            return False, "Failed to authenticate with Reddit"
        
        # Get the subreddit
        try:
            subreddit = reddit.subreddit(post.subreddit)
        except Exception as e:
            return False, f"Invalid subreddit '{post.subreddit}': {e}"
        
        # Submit the post to Reddit
        try:
            if post.content:
                # Text post
                reddit_submission = subreddit.submit(
                    title=post.title,
                    selftext=post.content
                )
            else:
                # For now, just text posts. You can add link posts later
                reddit_submission = subreddit.submit(
                    title=post.title,
                    selftext=""
                )
            
            # Update the post record with Reddit data
            post.reddit_post_id = reddit_submission.id
            post.reddit_url = f"https://reddit.com{reddit_submission.permalink}"
            post.status = Post.STATUS_POSTED
            post.save()
            
            print(f"Successfully posted to Reddit: {post.reddit_url}")
            return True, "Successfully posted to Reddit"
            
        except Exception as e:
            # Update post status to failed
            post.status = Post.STATUS_FAILED
            post.save()
            error_msg = f"Failed to submit to Reddit: {e}"
            print(error_msg)
            return False, error_msg
            
    except Exception as e:
        # Update post status to failed
        post.status = Post.STATUS_FAILED
        post.save()
        error_msg = f"Reddit posting error: {e}"
        print(error_msg)
        return False, error_msg

def get_user_reddit_accounts(user):
    """Get all active Reddit accounts for a user"""
    return RedditAccount.objects.filter(user=user, is_active=True)

def get_default_reddit_account(user):
    """Get the user's most recently created active Reddit account"""
    return RedditAccount.objects.filter(
        user=user, 
        is_active=True
    ).order_by('-created_at').first()