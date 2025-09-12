from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# Simple health check view
def health_check(request):
    return JsonResponse({
        "status": "ok", 
        "message": "Reddit Manager API is running"
    })

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # Health check endpoint (add this)
    path("health/", health_check, name="health_check"),
    
    # JWT Token endpoints
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    
    # Your app API endpoints
    path("api/auth/", include("users.urls", namespace="users")),
    path("api/reddit/", include("reddit_accounts.urls", namespace="reddit_accounts_api")),
    path("api/posts/", include("posts.urls", namespace="posts")),
    
    # Non-API URLs
    path("reddit/", include("reddit_accounts.urls", namespace="reddit_accounts_non_api")),
]