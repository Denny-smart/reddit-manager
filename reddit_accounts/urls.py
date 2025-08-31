from django.urls import path
from . import api_views

app_name = "reddit_accounts"

urlpatterns = [
    path("accounts/", api_views.reddit_accounts_list, name="api_list"),
    path("connect/", api_views.connect_reddit, name="api_connect"), 
    path("callback/", api_views.reddit_callback, name="api_callback"),
    path("disconnect/<int:pk>/", api_views.disconnect_reddit, name="api_disconnect"),
]