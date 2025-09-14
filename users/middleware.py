from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth.models import User
from django.db.models import ObjectDoesNotExist
import logging

logger = logging.getLogger(__name__)


class EmailVerificationMiddleware(MiddlewareMixin):
    """
    Middleware to check if a user has a verified email for protected endpoints.
    """
    
    # Endpoints that do not require email verification.
    EXEMPT_PATHS = [
        '/users/signup/',
        '/users/login/',
        '/users/verify-email/',
        '/users/resend-verification/',
        '/users/password-reset/',
        '/users/password-reset-confirm/',
        '/users/google/',
        '/api/token/',
        '/api/token/refresh/',
    ]
    
    def process_request(self, request):
        # Skip for exempt paths
        if any(request.path.startswith(path) for path in self.EXEMPT_PATHS):
            return None
        
        # Skip for CORS preflight requests
        if request.method == 'OPTIONS':
            return None
            
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return None # Let standard DRF auth handle it

        token_str = auth_header.split(' ')[1]
        
        try:
            # Use AccessToken to securely validate the token and get the user
            token = AccessToken(token_str)
            user = User.objects.get(id=token['user_id'])

            if hasattr(user, 'profile') and not user.profile.email_verified:
                return JsonResponse({
                    'detail': 'Email verification required. Please verify your email before accessing this resource.',
                    'email_verified': False,
                    'user_email': user.email
                }, status=403)
            
        except (InvalidToken, TokenError):
            # Let DRF handle invalid or expired tokens
            return None
        except ObjectDoesNotExist:
            logger.warning(f"User from token not found: user_id={token.get('user_id')}")
            return JsonResponse({'detail': 'User not found.'}, status=401)
        except Exception as e:
            logger.error(f"Email verification middleware error: {str(e)}")
            return None
            
        return None
