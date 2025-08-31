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
    path("api/auth/", include("users.urls")),  # Assuming you have users.urls for auth
    path("api/reddit/", include("reddit_accounts.urls")),
    path("api/posts/", include("posts.urls")),
    
    # Keep existing non-API URLs if needed
    path("reddit/", include("reddit_accounts.urls")),
]