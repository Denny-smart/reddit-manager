from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render

# Home page view
def home(request):
    return render(request, "home.html")  # now points to home.html, not base.html

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),  # Root URL (homepage)

    # Users app routes
    path("users/", include(("users.urls", "users"), namespace="users")),

    # Posts app routes
    path("posts/", include(("posts.urls", "posts"), namespace="posts")),

    # Reddit accounts app routes
    path("reddit/", include(("reddit_accounts.urls", "reddit_accounts"), namespace="reddit_accounts")),
]
