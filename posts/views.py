from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Post
from .forms import PostForm


@login_required
def create_post(request):
    if request.user.profile.role != "POSTER":
        return redirect("home")

    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            return redirect("post_list")
    else:
        form = PostForm()

    return render(request, "posts/create_post.html", {"form": form})


@login_required
def post_list(request):
    posts = Post.objects.all().order_by("-created_at")
    return render(request, "posts/post_list.html", {"posts": posts})
