# settings.py

from pathlib import Path
from datetime import timedelta
import environ
import os

# -----------------
# BASE DIRECTORY
# -----------------
BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------
# ENVIRONMENT VARIABLES
# -----------------
env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="dev-insecure-secret-key")
DEBUG = env.bool("DEBUG", default=True)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["127.0.0.1", "localhost"])

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
# CORS
# -----------------
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8080",
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
# SIMPLE JWT
# -----------------
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "JTI_CLAIM": "jti",
    "SIGNING_KEY": SECRET_KEY,
}

# -----------------
# DATABASE (SQLite for now)
# -----------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
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
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# -----------------
# DEFAULT PRIMARY KEY FIELD
# -----------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -----------------
# REDDIT API CREDENTIALS
# -----------------
REDDIT_CLIENT_ID = env.str("REDDIT_CLIENT_ID", default=None)
REDDIT_CLIENT_SECRET = env.str("REDDIT_CLIENT_SECRET", default=None)
REDDIT_REDIRECT_URI = env.str("REDDIT_REDIRECT_URI", default="http://localhost:8080/reddit/callback")
REDDIT_USER_AGENT = env.str("REDDIT_USER_AGENT", default="reddit-manager (by u/kiryke)")
