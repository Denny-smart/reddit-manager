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
env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[]) # Set a default empty list to avoid errors

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
    'corsheaders.middleware.CorsMiddleware', # Must be at the top
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware", # For serving static files in production
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",  
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

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
# CORS CONFIGURATION
# -----------------
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080",
    # This is your Vercel frontend URL, added here for production
    "https://reddit-sync-dash.vercel.app" 
]

CORS_ALLOW_CREDENTIALS = True

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
}

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
}

# -----------------
# DATABASE CONFIGURATION
# -----------------
# This will use SQLite in development and PostgreSQL in production
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///' + os.path.join(BASE_DIR, 'db.sqlite3'),
        conn_max_age=600
    )
}

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
TIME_ZONE = "Africa/Nairobi"   
USE_I18N = True
USE_TZ = True

# -----------------
# STATIC & MEDIA FILES
# -----------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# -----------------
# DEFAULT PRIMARY KEY FIELD
# -----------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -----------------
# MULTIPLE REDDIT APPS CONFIGURATION
# -----------------
def get_redirect_uri(app_suffix="1"):
    """
    Get the correct redirect URI based on environment.
    In production, use the production URL. In development, use localhost.
    """
    if DEBUG:
        # Development - use localhost
        return f"http://localhost:8080/reddit/callback/"
    else:
        # Production - use your Render URL
        return env.str(
            f"REDDIT_REDIRECT_URI_{app_suffix}_PROD", 
            default="https://reddit-manager.onrender.com/reddit/callback/"
        )

REDDIT_APPS = {
    'app1': {
        'CLIENT_ID': env.str("REDDIT_CLIENT_ID_1"),
        'CLIENT_SECRET': env.str("REDDIT_CLIENT_SECRET_1"),
        'REDIRECT_URI': get_redirect_uri("1"),
        'USER_AGENT': env.str("REDDIT_USER_AGENT_1"),
        'DISPLAY_NAME': 'Primary Reddit App (u/kiryke)',
    },
    'app2': {
        'CLIENT_ID': env.str("REDDIT_CLIENT_ID_2", default=None),
        'CLIENT_SECRET': env.str("REDDIT_CLIENT_SECRET_2", default=None),
        'REDIRECT_URI': get_redirect_uri("2"),
        'USER_AGENT': env.str("REDDIT_USER_AGENT_2", default="reddit-manager/0.1 by u/HuckleberryLanky6247"),
        'DISPLAY_NAME': 'Secondary Reddit App (u/HuckleberryLanky6247)',
    },
}

# -----------------
# BACKWARD COMPATIBILITY - Legacy Reddit API Settings
# (Keep existing code working)
# -----------------
REDDIT_CLIENT_ID = REDDIT_APPS['app1']['CLIENT_ID']
REDDIT_CLIENT_SECRET = REDDIT_APPS['app1']['CLIENT_SECRET']
REDDIT_REDIRECT_URI = REDDIT_APPS['app1']['REDIRECT_URI']
REDDIT_USER_AGENT = REDDIT_APPS['app1']['USER_AGENT']

# -----------------
# HELPER FUNCTIONS FOR REDDIT APPS
# -----------------
def get_reddit_app(app_name='app1'):
    """
    Get Reddit app configuration by name.
    """
    return REDDIT_APPS.get(app_name, REDDIT_APPS['app1'])

def get_available_reddit_apps():
    """
    Get list of all configured Reddit apps.
    
    Returns:
        list: List of tuples (app_key, display_name)
    """
    return [(key, config['DISPLAY_NAME']) for key, config in REDDIT_APPS.items() 
            if config['CLIENT_ID'] and config['CLIENT_SECRET']]

def is_reddit_app_configured(app_name):
    """
    Check if a Reddit app is properly configured.
    """
    if app_name not in REDDIT_APPS:
        return False
    
    app = REDDIT_APPS[app_name]
    return bool(app['CLIENT_ID'] and app['CLIENT_SECRET'])

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
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'reddit_accounts': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# -----------------
# DEVELOPMENT VS PRODUCTION SETTINGS
# -----------------
if DEBUG:
    # Development-specific settings
    CORS_ALLOW_ALL_ORIGINS = True
    LOGGING['loggers']['django']['level'] = 'DEBUG'
    ALLOWED_HOSTS = ['*']
else:
    # Production settings
    # Static file serving
    STATIC_URL = '/static/'
    STATIC_ROOT = BASE_DIR / 'staticfiles'
    
    # HTTPS and Security Headers
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

    # Force ALLOWED_HOSTS to be set in production
    if not ALLOWED_HOSTS:
        raise ValueError("ALLOWED_HOSTS must be set in production environment.")