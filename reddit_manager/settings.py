from pathlib import Path
from datetime import timedelta
import environ
import os
import dj_database_url
from django.core.exceptions import ImproperlyConfigured

# -----------------
# BASE DIRECTORY
# -----------------
BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------
# ENVIRONMENT VARIABLES
# -----------------
env = environ.Env()
# Read .env file only if it exists and we're in development
if os.path.exists(BASE_DIR / ".env"):
    environ.Env.read_env(BASE_DIR / ".env")

# Determine if we're in debug mode from environment
DEBUG = env.bool("DEBUG", default=False)

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
    'whitenoise.runserver_nostatic', # WhiteNoise for static files in production

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
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",  
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    'whitenoise.middleware.WhiteNoiseMiddleware', # For production static files
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
    "SIGNING_KEY": os.environ.get("SECRET_KEY", "dev-insecure-secret-key"),
    "ROTATE_REFRESH_TOKENS": True, 
    "BLACKLIST_AFTER_ROTATION": True,
}

# -----------------
# DEVELOPMENT VS PRODUCTION SETTINGS
# -----------------
if DEBUG:
    # Development-specific settings
    print("Running in DEVELOPMENT mode.")
    SECRET_KEY = env("SECRET_KEY", default="dev-insecure-secret-key")
    ALLOWED_HOSTS = ['*']
    CORS_ALLOW_ALL_ORIGINS = True
    
    # Use SQLite for development
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
    
    # More verbose logging in development
    LOGGING_LEVEL = "DEBUG"
    
    # Do not enforce secure cookies/headers in dev
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_SSL_REDIRECT = False
    X_FRAME_OPTIONS = "SAMEORIGIN"

    # CORS configuration for development
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "https://reddit-sync-dash.vercel.app"
    ]
    CORS_ALLOW_CREDENTIALS = True
    
else:
    # Production settings
    print("Running in PRODUCTION mode.")
    
    # SECURITY WARNING: For production, you MUST set a secure SECRET_KEY in env variables.
    SECRET_KEY = env("SECRET_KEY")
    if not SECRET_KEY or SECRET_KEY == "dev-insecure-secret-key":
        raise ImproperlyConfigured("The SECRET_KEY environment variable must be set in production.")

    # SECURITY WARNING: For production, you MUST set ALLOWED_HOSTS.
    ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")
    if not ALLOWED_HOSTS:
        raise ImproperlyConfigured("The ALLOWED_HOSTS environment variable must be set in production.")

    # PRODUCTION DATABASE: Use dj-database-url to parse DATABASE_URL
    DATABASES = {
        'default': dj_database_url.config(
            default='sqlite:///' + os.path.join(BASE_DIR, 'db.sqlite3'),
            conn_max_age=600
        )
    }

    # SECURE COOKIES AND HEADERS
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    X_FRAME_OPTIONS = "DENY"

    # CORS CONFIGURATION
    CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
    CORS_ALLOW_CREDENTIALS = True
    
    # LOGGING
    LOGGING_LEVEL = "INFO"

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
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Create static directory if it doesn't exist to prevent the warning.
os.makedirs(STATIC_ROOT, exist_ok=True)
if STATICFILES_DIRS:
    os.makedirs(STATICFILES_DIRS[0], exist_ok=True)

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# -----------------
# DEFAULT PRIMARY KEY FIELD
# -----------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -----------------
# MULTIPLE REDDIT APPS CONFIGURATION
# -----------------
REDDIT_APPS = {
    'app1': {
        'CLIENT_ID': env.str("REDDIT_CLIENT_ID_1", default=None),
        'CLIENT_SECRET': env.str("REDDIT_CLIENT_SECRET_1", default=None),
        'REDIRECT_URI': env.str("REDDIT_REDIRECT_URI_1", default="http://localhost:8080/reddit/callback/"),
        'USER_AGENT': env.str("REDDIT_USER_AGENT_1", default="reddit-manager/0.1 by u/kiryke"),
        'DISPLAY_NAME': 'Primary Reddit App (u/kiryke)',
    },
    'app2': {
        'CLIENT_ID': env.str("REDDIT_CLIENT_ID_2", default=None),
        'CLIENT_SECRET': env.str("REDDIT_CLIENT_SECRET_2", default=None),
        'REDIRECT_URI': env.str("REDDIT_REDIRECT_URI_2", default="http://localhost:8080/reddit/callback/"),
        'USER_AGENT': env.str("REDDIT_USER_AGENT_2", default="reddit-manager/0.1 by u/HuckleberryLanky6247"),
        'DISPLAY_NAME': 'Secondary Reddit App (u/HuckleberryLanky6247)',
    },
    # You can add more Reddit apps here by adding app3, app4, etc.
}

# -----------------
# BACKWARD COMPATIBILITY - Legacy Reddit API Settings
# (Keep existing code working)
# -----------------
REDDIT_CLIENT_ID = env.str("REDDIT_CLIENT_ID", default=REDDIT_APPS['app1']['CLIENT_ID'])
REDDIT_CLIENT_SECRET = env.str("REDDIT_CLIENT_SECRET", default=REDDIT_APPS['app1']['CLIENT_SECRET'])
REDDIT_REDIRECT_URI = env.str("REDDIT_REDIRECT_URI", default=REDDIT_APPS['app1']['REDIRECT_URI'])
REDDIT_USER_AGENT = env.str("REDDIT_USER_AGENT", default=REDDIT_APPS['app1']['USER_AGENT'])

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
            'level': LOGGING_LEVEL,
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
