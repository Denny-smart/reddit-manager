# posts/urls.py
from django.urls import path
from . import api_views

app_name = "posts"

urlpatterns = [
    path("", api_views.posts_list, name="api_list"),
    path("create/", api_views.posts_create, name="api_create"),
    path("posted/", api_views.posts_posted, name="api_posted"),
    path("<int:pk>/", api_views.posts_detail, name="api_detail"),
    path("<int:pk>/retry/", api_views.retry_post, name="api_retry"),  # Added missing retry endpoint
]