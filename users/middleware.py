from django.http import JsonResponse
from rest_framework import status

class EmailVerificationMiddleware:
    """
    Middleware to check email verification for authenticated users.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # URLs that don't require email verification
        self.exempt_urls = [
            '/api/auth/verify-email/',
            '/api/auth/resend-verification/',
            '/api/auth/logout/',
            '/api/auth/user/',  # Allow checking user status
            '/api/auth/signup/',  # Allow signup
            '/api/auth/login/',   # Allow login
            '/api/token/',        # Allow token endpoints
            '/admin/',
            '/health/',
        ]

    def __call__(self, request):
        # Check if user needs email verification
        if (request.user.is_authenticated and 
            hasattr(request.user, 'profile') and 
            not request.user.profile.email_verified and
            not any(request.path.startswith(url) for url in self.exempt_urls)):
            
            return JsonResponse({
                'error': 'Email verification required',
                'message': 'Please verify your email address to access this feature.',
                'email_verified': False
            }, status=status.HTTP_403_FORBIDDEN)

        response = self.get_response(request)
        return response