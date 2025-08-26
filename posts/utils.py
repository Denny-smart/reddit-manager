# posts/utils.py
import praw
from django.conf import settings

def get_reddit_instance_for_account(account):
    """
    account: reddit_accounts.RedditAccount instance (must contain refresh_token, client_id/secret if per-account)
    Adjust keys based on your reddit_accounts model.
    """
    # Example fields on account: refresh_token, client_id, client_secret, user_agent
    # If client id/secret are global, fetch from settings instead.
    client_id = getattr(account, "client_id", getattr(settings, "REDDIT_CLIENT_ID", None))
    client_secret = getattr(account, "client_secret", getattr(settings, "REDDIT_CLIENT_SECRET", None))
    refresh_token = getattr(account, "refresh_token", None)
    user_agent = getattr(account, "user_agent", getattr(settings, "REDDIT_USER_AGENT", "reddit-manager/0.1"))

    if not (client_id and client_secret and refresh_token):
        raise ValueError("Missing Reddit credentials for account")

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token,
        user_agent=user_agent,
    )
    return reddit

def publish_post_to_reddit(post):
    """
    Publishes a text post to Reddit with the account attached to the Post.reddit_account.
    Returns dict { "id": submission.id, "url": submission.url } on success.
    Raises exception on failure.
    """
    if not post.reddit_account:
        raise ValueError("No reddit account attached to this post")

    reddit = get_reddit_instance_for_account(post.reddit_account)
    subreddit = post.subreddit or "test"  # default fallback; you probably want to require a subreddit
    title = post.title
    content = post.content or ""

    # choose text post; if you want link/image, extend here
    submission = reddit.subreddit(subreddit).submit(title=title, selftext=content)
    return {"id": submission.id, "url": submission.url}
