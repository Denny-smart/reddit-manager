from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # JWT Token endpoints
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    
    # Your app API endpoints
    # Added namespaces to prevent URL naming conflicts
    path("api/auth/", include("users.urls", namespace="users")),
    path("api/reddit/", include("reddit_accounts.urls", namespace="reddit_accounts_api")),
    path("api/posts/", include("posts.urls", namespace="posts")),
    
    # Non-API URLs with a unique namespace
    path("reddit/", include("reddit_accounts.urls", namespace="reddit_accounts_non_api")),
]
