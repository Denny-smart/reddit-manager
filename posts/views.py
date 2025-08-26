# posts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Post
from .forms import PostForm
from .utils import publish_post_to_reddit  # helper we'll create below

@login_required
def post_list(request):
    posts = Post.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "posts/post_list.html", {"posts": posts})

@login_required
def posted_posts(request):
    posts = Post.objects.filter(user=request.user, status=Post.STATUS_POSTED).order_by("-created_at")
    return render(request, "posts/posted_posts.html", {"posts": posts})

@login_required
def create_post(request):
    if request.method == "POST":
        form = PostForm(request.POST, user=request.user)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user

            # Decide status and maybe post now
            if post.post_now:
                post.status = Post.STATUS_PENDING  # set pending while trying
                post.save()
                try:
                    result = publish_post_to_reddit(post)  # returns dict with id, url on success
                    post.reddit_post_id = result.get("id")
                    post.reddit_url = result.get("url")
                    post.status = Post.STATUS_POSTED
                except Exception as exc:
                    # mark failed and keep info for retry
                    post.status = Post.STATUS_FAILED
                    # optionally save error in a log model or post.error_text (not added)
                post.save()
            else:
                # scheduled for later
                post.status = Post.STATUS_SCHEDULED
                post.save()
            return redirect("posts:post_list")
    else:
        form = PostForm(user=request.user)
    return render(request, "posts/create_post.html", {"form": form})
