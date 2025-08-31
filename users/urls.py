# users/urls.py

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView
from .views import SignupView, UserDetailView, LogoutView

urlpatterns = [
    # JWT login endpoint
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    # User-related endpoints
    path('signup/', SignupView.as_view(), name='signup'),
    path('user/', UserDetailView.as_view(), name='user-detail'),
    path('logout/', LogoutView.as_view(), name='logout'),
]