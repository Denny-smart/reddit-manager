import secrets
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
import praw

from .models import RedditAccount

def _base_reddit():
    # PRAW instance without refresh_token (for generating auth URLs and exchanging code)
    return praw.Reddit(
        client_id=settings.REDDIT_CLIENT_ID,
        client_secret=settings.REDDIT_CLIENT_SECRET,
        redirect_uri=settings.REDDIT_REDIRECT_URI,
        user_agent=settings.REDDIT_USER_AGENT,
    )

@login_required
def reddit_accounts_list(request):
    accounts = RedditAccount.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "reddit_accounts/list.html", {"accounts": accounts})

@login_required
def connect_reddit(request):
    reddit = _base_reddit()
    state = secrets.token_urlsafe(32)
    request.session["reddit_oauth_state"] = state

    # Choose scopes you need (adjust as your app grows)
    scopes = ["identity", "read", "submit", "mysubreddits", "history"]

    # 'permanent' ensures we receive a refresh token for long-lived access
    auth_url = reddit.auth.url(scopes=scopes, state=state, duration="permanent")
    return redirect(auth_url)

@login_required
def reddit_callback(request):
    error = request.GET.get("error")
    if error:
        messages.error(request, f"Reddit OAuth error: {error}")
        return redirect("reddit_accounts:list")

    state = request.GET.get("state")
    code = request.GET.get("code")
    if not state or state != request.session.get("reddit_oauth_state"):
        messages.error(request, "State mismatch. Please try again.")
        return redirect("reddit_accounts:list")

    reddit = _base_reddit()
    try:
        # Exchange code -> refresh_token + set an active session on the PRAW instance
        refresh_token = reddit.auth.authorize(code)
    except Exception as e:
        messages.error(request, f"Authorization failed: {e}")
        return redirect("reddit_accounts:list")

    # Use the now-authorized instance to fetch the Reddit user
    me = reddit.user.me()
    if not me:
        messages.error(request, "Could not fetch Reddit user after auth.")
        return redirect("reddit_accounts:list")

    # Save or update the linked account
    scopes_now = ",".join(sorted(reddit.auth.scopes() or []))
    RedditAccount.objects.update_or_create(
        user=request.user,
        reddit_username=str(me.name),
        defaults={
            "reddit_id": getattr(me, "id", None),
            "refresh_token": refresh_token,
            "scopes": scopes_now,
            "is_active": True,
        },
    )
    messages.success(request, f"Connected Reddit account u/{me.name}.")
    return redirect("reddit_accounts:list")

@login_required
def disconnect_reddit(request, pk):
    account = get_object_or_404(RedditAccount, pk=pk, user=request.user)
    account.delete()
    messages.success(request, "Disconnected Reddit account.")
    return redirect("reddit_accounts:list")
