from django.urls import path
from . import api_views

app_name = "posts"

urlpatterns = [
    # List and Create
    path("", api_views.posts_list, name="api_list"),
    path("create/", api_views.posts_create, name="api_create"),
    
    # Filtered Lists
    path("posted/", api_views.posts_posted, name="api_posted"),
    path("scheduled/", api_views.posts_scheduled, name="api_scheduled"),
    path("failed/", api_views.posts_failed, name="api_failed"),  # Added failed posts endpoint
    
    # Single Post Operations
    path("<int:pk>/", api_views.posts_detail, name="api_detail"),
    path("<int:pk>/retry/", api_views.retry_post, name="api_retry"),
    path("<int:pk>/publish/", api_views.publish_post, name="api_publish"),
    path("<int:pk>/schedule/", api_views.schedule_post, name="api_schedule"),
]