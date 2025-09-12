# reddit_accounts/urls.py

from django.urls import path
from . import api_views

app_name = 'reddit_accounts'

urlpatterns = [
    # Reddit Apps Management
    path('apps/', api_views.reddit_apps_list, name='reddit_apps_list'),
    
    # Reddit Accounts Management
    path('accounts/', api_views.reddit_accounts_list, name='reddit_accounts_list'),
    path('connect/', api_views.connect_reddit, name='connect_reddit'),
    path('callback/', api_views.reddit_callback, name='reddit_callback'),
    path('accounts/<int:pk>/disconnect/', api_views.disconnect_reddit, name='disconnect_reddit'),
    path('accounts/<int:pk>/test/', api_views.test_reddit_connection, name='test_reddit_connection'),
    path('accounts/<int:pk>/switch-app/', api_views.switch_reddit_app, name='switch_reddit_app'),
]

# Backward compatibility routes (if you have existing URLs)
# These can be removed once you update your frontend
urlpatterns += [
    path('', api_views.reddit_accounts_list, name='reddit_accounts_list_compat'),
]