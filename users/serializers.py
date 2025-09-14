from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Profile, PasswordResetToken
from .utils import generate_reset_token, send_password_reset_email, verify_google_token, generate_username_from_email

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('role', 'profile_picture')

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'profile')

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'confirm_password', 'first_name', 'last_name')

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        
        # Validate password strength
        try:
            validate_password(data['password'])
        except ValidationError as e:
            raise serializers.ValidationError({"password": e.messages})
            
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address.")

    def save(self):
        email = self.validated_data['email']
        user = User.objects.get(email=email)
        
        # Invalidate any existing tokens
        PasswordResetToken.objects.filter(user=user, used=False).update(used=True)
        
        # Create new token
        token = generate_reset_token()
        PasswordResetToken.objects.create(user=user, token=token)
        
        # Send email
        send_password_reset_email(user, token)
        
        return user

class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    token = serializers.CharField(max_length=32)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        
        # Validate password strength
        try:
            validate_password(data['new_password'])
        except ValidationError as e:
            raise serializers.ValidationError({"new_password": e.messages})
        
        # Validate token
        try:
            user = User.objects.get(email=data['email'])
            reset_token = PasswordResetToken.objects.get(
                user=user, 
                token=data['token']
            )
            
            if not reset_token.is_valid():
                raise serializers.ValidationError("Invalid or expired reset token.")
                
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email address.")
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError("Invalid reset token.")
            
        return data

    def save(self):
        email = self.validated_data['email']
        token = self.validated_data['token']
        new_password = self.validated_data['new_password']
        
        user = User.objects.get(email=email)
        reset_token = PasswordResetToken.objects.get(user=user, token=token)
        
        # Update password
        user.set_password(new_password)
        user.save()
        
        # Mark token as used
        reset_token.used = True
        reset_token.save()
        
        return user

class GoogleAuthSerializer(serializers.Serializer):
    google_token = serializers.CharField()

    def validate_google_token(self, value):
        google_user_info = verify_google_token(value)
        if not google_user_info:
            raise serializers.ValidationError("Invalid Google token.")
        return value

    def save(self):
        google_token = self.validated_data['google_token']
        google_user_info = verify_google_token(google_token)
        
        if not google_user_info['email_verified']:
            raise serializers.ValidationError("Email not verified by Google.")
        
        # Check if user exists with this Google ID
        try:
            profile = Profile.objects.get(google_id=google_user_info['google_id'])
            return profile.user
        except Profile.DoesNotExist:
            pass
        
        # Check if user exists with this email
        try:
            user = User.objects.get(email=google_user_info['email'])
            # Link Google account to existing user
            user.profile.google_id = google_user_info['google_id']
            user.profile.profile_picture = google_user_info.get('picture', '')
            user.profile.save()
            
            # Update user info if not set
            if not user.first_name and google_user_info.get('first_name'):
                user.first_name = google_user_info['first_name']
            if not user.last_name and google_user_info.get('last_name'):
                user.last_name = google_user_info['last_name']
                user.save()
                
            return user
        except User.DoesNotExist:
            pass
        
        # Create new user
        username = generate_username_from_email(google_user_info['email'])
        user = User.objects.create_user(
            username=username,
            email=google_user_info['email'],
            first_name=google_user_info.get('first_name', ''),
            last_name=google_user_info.get('last_name', ''),
            password=None  # No password for OAuth users
        )
        
        # Update profile with Google info
        user.profile.google_id = google_user_info['google_id']
        user.profile.profile_picture = google_user_info.get('picture', '')
        user.profile.save()
        
        return user