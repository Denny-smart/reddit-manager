from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render

# Home page view
def home(request):
    return render(request, "home.html")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),  # Root URL for homepage

    # API routes
    path("api/auth/", include(("users.urls", "users"), namespace="users")),
    path("api/posts/", include(("posts.urls", "posts"), namespace="posts")),
    path("api/reddit/", include(("reddit_accounts.urls", "reddit_accounts"), namespace="reddit_accounts")),
]
