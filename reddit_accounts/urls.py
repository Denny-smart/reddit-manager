from django.urls import path
from . import views

app_name = "reddit_accounts"

urlpatterns = [
    path("accounts/", views.reddit_accounts_list, name="list"),
    path("connect/", views.connect_reddit, name="connect"),
    path("callback/", views.reddit_callback, name="callback"),
    path("disconnect/<int:pk>/", views.disconnect_reddit, name="disconnect"),
]
