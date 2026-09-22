"""
Django settings for portfolio backend.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

from django.core.exceptions import ImproperlyConfigured


def _str_to_bool(val, default=False):
    if val is None:
        return default
    return str(val).strip().lower() in ('true', '1', 'yes', 't')


# Load environment variables from backend/.env
dotenv_path = BASE_DIR / '.env'
if dotenv_path.exists():
    load_dotenv(dotenv_path)

DEBUG = _str_to_bool(os.getenv('DEBUG', 'True'), default=True)

# Security: SECRET_KEY configuration
_raw_secret = os.getenv('SECRET_KEY')
if not DEBUG:
    if not _raw_secret or _raw_secret.startswith('django-insecure-') or len(_raw_secret) < 50:
        raise ImproperlyConfigured(
            "Production security configuration error: A valid, secure SECRET_KEY "
            "(minimum 50 characters, not starting with 'django-insecure-') "
            "must be configured in the environment when DEBUG=False."
        )
    SECRET_KEY = _raw_secret
else:
    SECRET_KEY = _raw_secret or 'django-insecure-portfolio-dev-secret-key-replace-in-production'

allowed_hosts_raw = os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost')
ALLOWED_HOSTS = [h.strip() for h in allowed_hosts_raw.split(',') if h.strip()]

# Application definition
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party apps
    'corsheaders',
    'rest_framework',
    # Local apps
    'api.apps.ApiConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
            BASE_DIR.parent / 'frontend',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Minimal database setup for Django internal auth and sessions
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR.parent / 'frontend',
]

# Media files (uploaded PDFs, images)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
FILE_STORAGE_PROVIDER = os.getenv('FILE_STORAGE_PROVIDER', 'local')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Session, CSRF and Production SSL Security
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 86400 * 7  # 7 days

CSRF_COOKIE_HTTPONLY = False  # Must be readable by frontend JS to attach X-CSRFToken
CSRF_COOKIE_SAMESITE = 'Lax'

# Reverse Proxy SSL Header (for Render / Heroku / Cloud load balancers)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_CONTENT_TYPE_NOSNIFF = True

if not DEBUG:
    SECURE_SSL_REDIRECT = _str_to_bool(os.getenv('SECURE_SSL_REDIRECT', 'True'), default=True)
    SESSION_COOKIE_SECURE = _str_to_bool(os.getenv('SESSION_COOKIE_SECURE', 'True'), default=True)
    CSRF_COOKIE_SECURE = _str_to_bool(os.getenv('CSRF_COOKIE_SECURE', 'True'), default=True)
    SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = _str_to_bool(os.getenv('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'True'), default=True)
    SECURE_HSTS_PRELOAD = _str_to_bool(os.getenv('SECURE_HSTS_PRELOAD', 'True'), default=True)
else:
    SECURE_SSL_REDIRECT = _str_to_bool(os.getenv('SECURE_SSL_REDIRECT', 'False'), default=False)
    SESSION_COOKIE_SECURE = _str_to_bool(os.getenv('SESSION_COOKIE_SECURE', 'False'), default=False)
    CSRF_COOKIE_SECURE = _str_to_bool(os.getenv('CSRF_COOKIE_SECURE', 'False'), default=False)
    SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '0'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = _str_to_bool(os.getenv('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'False'), default=False)
    SECURE_HSTS_PRELOAD = _str_to_bool(os.getenv('SECURE_HSTS_PRELOAD', 'False'), default=False)

csrf_trusted_raw = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://127.0.0.1:8000,http://localhost:8000')
CSRF_TRUSTED_ORIGINS = [o.strip() for o in csrf_trusted_raw.split(',') if o.strip()]

# Cache for rate limiting and session protection
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'portfolio-cache',
    }
}

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
}

if DEBUG:
    REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'].append(
        'rest_framework.renderers.BrowsableAPIRenderer'
    )

# CORS Configuration
CORS_ALLOW_ALL_ORIGINS = False
cors_origins_raw = os.getenv('CORS_ALLOWED_ORIGINS', '')
if cors_origins_raw:
    CORS_ALLOWED_ORIGINS = [
        origin.strip() for origin in cors_origins_raw.split(',') if origin.strip()
    ]
else:
    CORS_ALLOWED_ORIGINS = [
        'http://127.0.0.1:5500',
        'http://localhost:5500',
        'http://127.0.0.1:3000',
        'http://localhost:3000',
        'http://127.0.0.1:8000',
        'http://localhost:8000',
    ]

# MongoDB Atlas Configuration
MONGODB_URI = os.getenv('MONGODB_URI', '')
MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'portfolio')

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '[%(asctime)s] %(levelname)s %(name)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'loggers': {
        'api': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
