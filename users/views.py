from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import Profile, EmailVerificationToken, PasswordResetToken
from .serializers import (
    SignupSerializer, 
    UserSerializer, 
    EmailVerificationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    GoogleAuthSerializer,
    LoginSerializer,
)
from .utils import (
    generate_reset_token, 
    send_password_reset_email,
    send_verification_email,
)
import logging
import secrets
from django.db import transaction

logger = logging.getLogger(__name__)


class SignupView(generics.CreateAPIView):
    """
    Registers a new user.
    """
    queryset = User.objects.all()
    serializer_class = SignupSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        with transaction.atomic():
            user = serializer.save()
            # Generate and save a verification token
            token = secrets.token_hex(16)
            EmailVerificationToken.objects.create(user=user, token=token)
            # Send verification email asynchronously
            # This is a good place to use a task queue like Celery
            send_verification_email(user, token)
            logger.info(f"New user signed up: {user.username}. Verification email sent.")


class LoginView(APIView):
    """
    Custom login view to check for email verification before issuing tokens.
    """
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        if not user.profile.email_verified:
            return Response({
                'detail': 'Email not verified. Please check your inbox for a verification link.',
                'email_verified': False
            }, status=status.HTTP_403_FORBIDDEN)
        
        refresh = RefreshToken.for_user(user)
        access_token = AccessToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(access_token),
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)


class UserDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieves and updates the authenticated user's details.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class LogoutView(APIView):
    """
    Logout a user by blacklisting their refresh token.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class EmailVerificationView(APIView):
    """
    Verify user email with a token.
    """
    permission_classes = [AllowAny]
    serializer_class = EmailVerificationSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        token_str = serializer.validated_data['token']

        try:
            with transaction.atomic():
                token_obj = get_object_or_404(EmailVerificationToken, token=token_str)

                if not token_obj.is_valid():
                    token_obj.delete()
                    return Response({'detail': 'Token has expired.'}, status=status.HTTP_400_BAD_REQUEST)

                user = token_obj.user
                profile = user.profile
                profile.email_verified = True
                profile.save()
                
                # Delete token to prevent reuse
                token_obj.delete()
                
                return Response({'detail': 'Email successfully verified.'}, status=status.HTTP_200_OK)
        
        except EmailVerificationToken.DoesNotExist:
            return Response({'detail': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Email verification error: {str(e)}")
            return Response({'detail': 'An error occurred during verification.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResendVerificationView(APIView):
    """
    Resend verification email.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'detail': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            if user.profile.email_verified:
                return Response({'detail': 'Email is already verified.'}, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                # Delete old tokens
                EmailVerificationToken.objects.filter(user=user).delete()
                # Create and send new token
                token = secrets.token_hex(16)
                EmailVerificationToken.objects.create(user=user, token=token)
                send_verification_email(user, token)
                
                logger.info(f"Verification email resent to {user.email}")
            return Response({'detail': 'Verification email has been resent.'}, status=status.HTTP_200_OK)
        
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error resending verification email for {email}: {str(e)}")
            return Response({'detail': 'An error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PasswordResetRequestView(APIView):
    """
    Request a password reset.
    """
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            with transaction.atomic():
                PasswordResetToken.objects.filter(user=user).delete()
                token = generate_reset_token()
                PasswordResetToken.objects.create(user=user, token=token)
                
                send_password_reset_email(user, token)
            
            return Response({'detail': 'If an account exists with this email, a password reset link has been sent.'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'detail': 'If an account exists with this email, a password reset link has been sent.'}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """
    Confirm password reset with a token and new password.
    """
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        token_str = serializer.validated_data['token']
        password = serializer.validated_data['password']
        
        try:
            with transaction.atomic():
                token_obj = get_object_or_404(PasswordResetToken, token=token_str)
                
                if not token_obj.is_valid():
                    token_obj.delete()
                    return Response({'detail': 'Token has expired.'}, status=status.HTTP_400_BAD_REQUEST)

                user = token_obj.user
                user.set_password(password)
                user.save()
                
                token_obj.delete()
                
            return Response({'detail': 'Password has been reset successfully.'}, status=status.HTTP_200_OK)
        except PasswordResetToken.DoesNotExist:
            return Response({'detail': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Password reset confirmation error: {str(e)}")
            return Response({'detail': 'An error occurred during password reset.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GoogleAuthView(APIView):
    """
    Authenticates a user with a Google ID token.
    """
    permission_classes = [AllowAny]
    serializer_class = GoogleAuthSerializer
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Issue JWT tokens for the authenticated Google user
        refresh = RefreshToken.for_user(user)
        access_token = AccessToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(access_token),
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)
