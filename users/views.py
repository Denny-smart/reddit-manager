from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import logout
from django.contrib.auth.models import User
from .serializers import (
    SignupSerializer, 
    UserSerializer, 
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    GoogleAuthSerializer
)
import logging

logger = logging.getLogger(__name__)

def get_tokens_for_user(user):
    """Generate JWT tokens for user."""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class SignupView(generics.CreateAPIView):
    """
    Handles user signup.
    """
    queryset = User.objects.all()
    serializer_class = SignupSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens for the new user
        tokens = get_tokens_for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': tokens,
            'message': 'Account created successfully.'
        }, status=status.HTTP_201_CREATED)

class UserDetailView(generics.RetrieveAPIView):
    """
    Returns authenticated user details.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class LogoutView(APIView):
    """
    Logs out the user.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetRequestView(APIView):
    """
    Request password reset email.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                logger.info(f"Password reset requested for user: {user.email}")
                return Response({
                    "message": "If an account with that email exists, a password reset link has been sent."
                }, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Error processing password reset request: {str(e)}")
                return Response({
                    "message": "If an account with that email exists, a password reset link has been sent."
                }, status=status.HTTP_200_OK)
        
        # Don't reveal whether email exists or not
        return Response({
            "message": "If an account with that email exists, a password reset link has been sent."
        }, status=status.HTTP_200_OK)

class PasswordResetConfirmView(APIView):
    """
    Confirm password reset with token.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                logger.info(f"Password reset successful for user: {user.email}")
                return Response({
                    "message": "Password has been reset successfully."
                }, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Error confirming password reset: {str(e)}")
                return Response({
                    "error": "An error occurred while resetting your password."
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GoogleAuthView(APIView):
    """
    Authenticate user with Google OAuth token.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                tokens = get_tokens_for_user(user)
                
                logger.info(f"Google authentication successful for user: {user.email}")
                
                return Response({
                    'user': UserSerializer(user).data,
                    'tokens': tokens,
                    'message': 'Authentication successful.'
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                logger.error(f"Error in Google authentication: {str(e)}")
                return Response({
                    "error": "Authentication failed."
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)