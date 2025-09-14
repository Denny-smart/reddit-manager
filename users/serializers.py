from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Profile, EmailVerificationToken
from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
from .utils import verify_google_token, generate_username_from_email


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('role', 'email_verified', 'google_id', 'profile_picture')


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'profile')


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'confirm_password', 'first_name', 'last_name')

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def validate_email(self, value):
        """Check if email already exists."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_password(self, value):
        """Add password strength validation."""
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return value

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        
        # Profile is automatically created by signal with default POSTER role
        # and email_verified=False
        
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login with username/email and password.
    """
    username_or_email = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        username_or_email = data.get('username_or_email')
        password = data.get('password')

        if not username_or_email or not password:
            raise serializers.ValidationError("Both username/email and password are required.")

        # Try to authenticate with username first
        user = authenticate(request=self.context.get('request'), username=username_or_email, password=password)

        if not user:
            # If username authentication fails, try with email
            try:
                user = User.objects.get(email=username_or_email)
                user = authenticate(request=self.context.get('request'), username=user.username, password=password)
            except User.DoesNotExist:
                pass
        
        if not user or not user.is_active:
            raise serializers.ValidationError("Invalid credentials or user is inactive.")
            
        data['user'] = user
        return data


class EmailVerificationSerializer(serializers.Serializer):
    """
    Serializer for email verification.
    """
    token = serializers.CharField(max_length=32, required=True)
    
    def validate_token(self, value):
        if not value:
            raise serializers.ValidationError("Verification token is required.")
        if len(value) != 32:
            raise serializers.ValidationError("Invalid verification token format.")
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for password reset request.
    """
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            pass
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for password reset confirmation.
    """
    token = serializers.CharField(max_length=32, required=True)
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data
    
    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return value


class GoogleAuthSerializer(serializers.Serializer):
    """
    Serializer for Google OAuth authentication.
    """
    token = serializers.CharField(required=True)
    
    def validate_token(self, value):
        if not value:
            raise serializers.ValidationError("Google token is required.")
        return value
    
    def save(self):
        """
        Verify Google token and create/get user.
        """
        token = self.validated_data['token']
        
        # Use the utility function to verify token
        user_info = verify_google_token(token)
        
        if not user_info:
            raise serializers.ValidationError("Invalid Google token.")
        
        try:
            google_id = user_info['google_id']
            email = user_info['email']
            first_name = user_info['first_name']
            last_name = user_info['last_name']
            profile_picture = user_info['picture']
            
            # Check if user already exists by email
            try:
                user = User.objects.get(email=email)
                
                # Update profile with Google info if not already set
                profile = user.profile
                if not profile.google_id:
                    profile.google_id = google_id
                    profile.email_verified = True
                    if profile_picture and not profile.profile_picture:
                        profile.profile_picture = profile_picture
                    profile.save()
                    
            except User.DoesNotExist:
                # Create new user using utility function
                username = generate_username_from_email(email)
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=None
                )
                
                # Update the automatically created profile
                profile = user.profile
                profile.google_id = google_id
                profile.email_verified = True
                profile.role = 'POSTER'
                if profile_picture:
                    profile.profile_picture = profile_picture
                profile.save()
            
            return user
            
        except Exception as e:
            raise serializers.ValidationError(f"Google authentication failed: {str(e)}")
