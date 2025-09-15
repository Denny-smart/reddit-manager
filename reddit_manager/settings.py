from pathlib import Path
from datetime import timedelta
import environ
import os
import dj_database_url

# -----------------
# BASE DIRECTORY
# -----------------
BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------
# ENVIRONMENT VARIABLES
# -----------------
env = environ.Env(
    # Set casting and default values
    DEBUG=(bool, False),
    SECRET_KEY=(str, ''),
    ALLOWED_HOSTS=(list, []),
)

# Read .env file if it exists (for local development)
env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(env_file)

# -----------------
# CORE DJANGO SETTINGS
# -----------------
SECRET_KEY = env('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable must be set")

DEBUG = env.bool('DEBUG', default=False)

# Handle ALLOWED_HOSTS properly
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])
if not DEBUG and not ALLOWED_HOSTS:
    # In production, require ALLOWED_HOSTS to be explicitly set
    ALLOWED_HOSTS = ['reddit-manager.onrender.com', 'reddit-sync-dash.vercel.app']

# -----------------
# INSTALLED APPS
# -----------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps for API functionality
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',

    # Local apps
    'users',
    'reddit_accounts',
    'posts',
    'schedules',
]

# -----------------
# MIDDLEWARE
# -----------------
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",  
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    'users.middleware.EmailVerificationMiddleware',
]

# -----------------
# TEMPLATES
# -----------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# -----------------
# URLS & WSGI
# -----------------
ROOT_URLCONF = "reddit_manager.urls"
WSGI_APPLICATION = "reddit_manager.wsgi.application"

# -----------------
# DATABASE CONFIGURATION
# -----------------
database_url = env.str('DATABASE_URL', default='')

if database_url and database_url.strip():
    # Production - use the provided DATABASE_URL
    try:
        DATABASES = {
            'default': dj_database_url.parse(database_url)
        }
        # Add production optimizations
        if not DEBUG:
            DATABASES['default']['CONN_MAX_AGE'] = 600
            DATABASES['default']['CONN_HEALTH_CHECKS'] = True
    except Exception as e:
        print(f"Error parsing DATABASE_URL: {e}")
        # This should not happen in production, but provides a fallback
        raise ValueError(f"Invalid DATABASE_URL configuration: {e}")
else:
    # Development - use SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
            'OPTIONS': {
                'timeout': 300,
            }
        }
    }

# -----------------
# CORS CONFIGURATION
# -----------------
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ]
else:
    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOWED_ORIGINS = [
        "https://reddit-sync-dash.vercel.app",
        "https://reddit-manager.onrender.com",
    ]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# -----------------
# CSRF CONFIGURATION
# -----------------
CSRF_TRUSTED_ORIGINS = [
    "https://reddit-sync-dash.vercel.app",
    "https://reddit-manager.onrender.com",
]

if DEBUG:
    CSRF_TRUSTED_ORIGINS.extend([
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ])

# -----------------
# DJANGO REST FRAMEWORK
# -----------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# Add browsable API renderer only in debug mode
if DEBUG:
    REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'].append('rest_framework.renderers.BrowsableAPIRenderer')

# -----------------
# SIMPLE JWT CONFIGURATION
# -----------------
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15), 
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),   
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "JTI_CLAIM": "jti",
    "SIGNING_KEY": SECRET_KEY,
    "ROTATE_REFRESH_TOKENS": True, 
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
}

# -----------------
# FRONTEND & BACKEND URLS
# -----------------
FRONTEND_URL = env.str('FRONTEND_URL', 
    'https://reddit-sync-dash.vercel.app' if not DEBUG else 'http://localhost:3000'
)
BACKEND_URL = env.str('BACKEND_URL', 
    'https://reddit-manager.onrender.com' if not DEBUG else 'http://localhost:8000'
)

# -----------------
# EMAIL CONFIGURATION
# -----------------
if DEBUG:
    # Development - Console backend (prints emails to console)
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    # Production - SMTP backend
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = env.str('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = env.int('EMAIL_PORT', 587)
    EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', True)
    EMAIL_HOST_USER = env.str('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = env.str('EMAIL_HOST_PASSWORD', '')
    
    # Validate email settings in production
    if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
        print("WARNING: Email settings not configured. Email functionality will not work.")

DEFAULT_FROM_EMAIL = env.str('DEFAULT_FROM_EMAIL', 'noreply@reddit-manager.com')
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# -----------------
# GOOGLE OAUTH CONFIGURATION
# -----------------
GOOGLE_CLIENT_ID = env.str('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = env.str('GOOGLE_CLIENT_SECRET', '')

# Legacy variables (for backward compatibility)
GOOGLE_OAUTH2_CLIENT_ID = GOOGLE_CLIENT_ID
GOOGLE_OAUTH2_CLIENT_SECRET = GOOGLE_CLIENT_SECRET

# Token expiry settings
PASSWORD_RESET_TIMEOUT = env.int('PASSWORD_RESET_TIMEOUT', 3600)  # 1 hour
EMAIL_VERIFICATION_TIMEOUT = env.int('EMAIL_VERIFICATION_TIMEOUT', 600)  # 10 minutes

# -----------------
# REDDIT API CONFIGURATION
# -----------------
def get_redirect_uri(app_suffix="1"):
    """Get the correct redirect URI based on environment."""
    if DEBUG:
        return f"http://localhost:8080/reddit/callback/"
    else:
        return env.str(
            f"REDDIT_REDIRECT_URI_{app_suffix}_PROD", 
            default="https://reddit-manager.onrender.com/reddit/callback/"
        )

# Check if Reddit API is configured
REDDIT_API_CONFIGURED = all([
    env.str("REDDIT_CLIENT_ID_1", default="").strip(),
    env.str("REDDIT_CLIENT_SECRET_1", default="").strip(),
    env.str("REDDIT_USER_AGENT_1", default="").strip(),
])

if REDDIT_API_CONFIGURED:
    REDDIT_APPS = {
        'app1': {
            'CLIENT_ID': env.str("REDDIT_CLIENT_ID_1"),
            'CLIENT_SECRET': env.str("REDDIT_CLIENT_SECRET_1"),
            'REDIRECT_URI': get_redirect_uri("1"),
            'USER_AGENT': env.str("REDDIT_USER_AGENT_1"),
            'DISPLAY_NAME': env.str("REDDIT_APP_1_NAME", 'Primary Reddit App'),
        },
        'app2': {
            'CLIENT_ID': env.str("REDDIT_CLIENT_ID_2", default=""),
            'CLIENT_SECRET': env.str("REDDIT_CLIENT_SECRET_2", default=""),
            'REDIRECT_URI': get_redirect_uri("2"),
            'USER_AGENT': env.str("REDDIT_USER_AGENT_2", default="RedditManager/1.0 by SecondaryUser"),
            'DISPLAY_NAME': env.str("REDDIT_APP_2_NAME", 'Secondary Reddit App'),
        },
    }
else:
    # Fallback configuration when Reddit API is not set up
    if not DEBUG:
        print("WARNING: Reddit API credentials not configured.")
    
    REDDIT_APPS = {
        'app1': {
            'CLIENT_ID': 'not_configured',
            'CLIENT_SECRET': 'not_configured',
            'REDIRECT_URI': get_redirect_uri("1"),
            'USER_AGENT': 'RedditManager/1.0 by NotConfigured',
            'DISPLAY_NAME': 'Primary Reddit App (Not Configured)',
        },
        'app2': {
            'CLIENT_ID': 'not_configured',
            'CLIENT_SECRET': 'not_configured', 
            'REDIRECT_URI': get_redirect_uri("2"),
            'USER_AGENT': 'RedditManager/1.0 by NotConfigured',
            'DISPLAY_NAME': 'Secondary Reddit App (Not Configured)',
        },
    }

# Legacy Reddit settings (backward compatibility)
REDDIT_CLIENT_ID = REDDIT_APPS['app1']['CLIENT_ID']
REDDIT_CLIENT_SECRET = REDDIT_APPS['app1']['CLIENT_SECRET']
REDDIT_REDIRECT_URI = REDDIT_APPS['app1']['REDIRECT_URI']
REDDIT_USER_AGENT = REDDIT_APPS['app1']['USER_AGENT']

# -----------------
# HELPER FUNCTIONS FOR REDDIT APPS
# -----------------
def get_reddit_app(app_name='app1'):
    """Get Reddit app configuration by name."""
    return REDDIT_APPS.get(app_name, REDDIT_APPS['app1'])

def get_available_reddit_apps():
    """Get list of all configured Reddit apps."""
    return [(key, config['DISPLAY_NAME']) for key, config in REDDIT_APPS.items() 
            if config['CLIENT_ID'] != 'not_configured']

def is_reddit_app_configured(app_name):
    """Check if a Reddit app is properly configured."""
    if app_name not in REDDIT_APPS:
        return False
    
    app = REDDIT_APPS[app_name]
    return app['CLIENT_ID'] != 'not_configured' and bool(app['CLIENT_ID'] and app['CLIENT_SECRET'])

# -----------------
# PASSWORD VALIDATION
# -----------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# -----------------
# INTERNATIONALIZATION
# -----------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = env.str('TIME_ZONE', 'Africa/Nairobi')
USE_I18N = True
USE_TZ = True

# -----------------
# STATIC & MEDIA FILES
# -----------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Only include STATICFILES_DIRS if the directory exists
static_dir = BASE_DIR / "static"
if static_dir.exists():
    STATICFILES_DIRS = [static_dir]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Static files configuration for production
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# -----------------
# DEFAULT PRIMARY KEY FIELD
# -----------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -----------------
# LOGGING CONFIGURATION
# -----------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose' if not DEBUG else 'simple',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        } if (BASE_DIR / 'logs').exists() or DEBUG else None,
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'] + (['file'] if (BASE_DIR / 'logs').exists() or DEBUG else []),
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'reddit_accounts': {
            'handlers': ['console'] + (['file'] if (BASE_DIR / 'logs').exists() or DEBUG else []),
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'users': {
            'handlers': ['console'] + (['file'] if (BASE_DIR / 'logs').exists() or DEBUG else []),
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# Remove None values from handlers
LOGGING['handlers'] = {k: v for k, v in LOGGING['handlers'].items() if v is not None}

# Create logs directory if it doesn't exist and we're in debug mode
if DEBUG:
    os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# -----------------
# SECURITY SETTINGS
# -----------------
if not DEBUG:
    # Production security settings
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', 31536000)  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    X_FRAME_OPTIONS = 'DENY'
    
    # Additional security headers
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
else:
    # Development settings
    CORS_ALLOW_ALL_ORIGINS = True

# -----------------
# CACHE CONFIGURATION
# -----------------
if not DEBUG:
    # Use Redis or database caching in production
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'cache_table',
        }
    }
else:
    # Use dummy cache in development
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }

# -----------------
# SESSION CONFIGURATION
# -----------------
SESSION_COOKIE_AGE = env.int('SESSION_COOKIE_AGE', 1209600)  # 2 weeks
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

if not DEBUG:
    SESSION_COOKIE_SECURE = True

# -----------------
# ADDITIONAL PRODUCTION SETTINGS
# -----------------
if not DEBUG:
    # Ensure critical environment variables are set
    required_env_vars = ['SECRET_KEY']
    missing_vars = [var for var in required_env_vars if not env.str(var, default='')]
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    # Email configuration validation
    if env.str('EMAIL_HOST_USER', '') and not env.str('EMAIL_HOST_PASSWORD', ''):
        print("WARNING: EMAIL_HOST_USER is set but EMAIL_HOST_PASSWORD is missing")

# -----------------
# HEALTH CHECK ENDPOINT
# -----------------
HEALTH_CHECK_URL = env.str('HEALTH_CHECK_URL', '/health/')

# -----------------
# API RATE LIMITING (if using django-ratelimit)
# -----------------
RATELIMIT_ENABLE = env.bool('RATELIMIT_ENABLE', not DEBUG)
RATELIMIT_USE_CACHE = 'default'