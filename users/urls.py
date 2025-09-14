from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    SignupView, 
    UserDetailView, 
    LogoutView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    GoogleAuthView,
    EmailVerificationView,
    ResendVerificationView,
    LoginView, # Added custom login view
)

app_name = 'users'

urlpatterns = [
    # JWT authentication endpoints
    # JWT's default login view for token generation
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Custom login view with email verification check
    path('login/', LoginView.as_view(), name='custom-login'),
    
    # User management endpoints
    path('signup/', SignupView.as_view(), name='signup'),
    path('user/', UserDetailView.as_view(), name='user-detail'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Email verification endpoints
    path('verify-email/', EmailVerificationView.as_view(), name='verify-email'),
    path('resend-verification/', ResendVerificationView.as_view(), name='resend-verification'),
    
    # Password reset endpoints
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    
    # Google OAuth endpoint
    path('google/', GoogleAuthView.as_view(), name='google-auth'),
]
