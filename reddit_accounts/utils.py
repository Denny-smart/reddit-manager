import praw
from django.conf import settings

def reddit_for_account(account):
    return praw.Reddit(
        client_id=settings.REDDIT_CLIENT_ID,
        client_secret=settings.REDDIT_CLIENT_SECRET,
        user_agent=settings.REDDIT_USER_AGENT,
        refresh_token=account.refresh_token,  # PRAW auto-refreshes access tokens
    )
