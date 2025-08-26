from pathlib import Path
import environ

# -----------------
# BASE DIRECTORY
# -----------------
BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------
# ENVIRONMENT VARIABLES
# -----------------
env = environ.Env(
    DEBUG=(bool, False)
)
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
    'users',
    'reddit_accounts',
    'posts',
    'schedules',
]

# -----------------
# MIDDLEWARE
# -----------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",  
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# -----------------
# URLS & WSGI
# -----------------
ROOT_URLCONF = "reddit_manager.urls"
WSGI_APPLICATION = "reddit_manager.wsgi.application"

# -----------------
# TEMPLATES
# -----------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # global templates folder
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
# DJANGO REST FRAMEWORK
# -----------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

LOGIN_URL = '/users/login/'
LOGIN_REDIRECT_URL = "/users/"      # where users go after login
LOGOUT_REDIRECT_URL = '/login/'  # where users go after logout
LOGIN_URL = '/login/'

# settings.py
import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent

# super-light .env loader (optional; fine for dev)
env_file = BASE_DIR / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if line.strip() and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET")
REDDIT_REDIRECT_URI = os.environ.get("REDDIT_REDIRECT_URI", "http://127.0.0.1:8000/reddit/callback/")
REDDIT_USER_AGENT = os.environ.get("REDDIT_USER_AGENT", "reddit-manager (by u/kiryke)")

