"""
Django settings for party_management project.
"""

from pathlib import Path
import os
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
# NOTE: Replace this with a secure value pulled from an environment variable in production!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-@2w$&pr_dv^1h-efp=@in5w7+hckqql(6v=0e6#6on9gesmjn)')

# FIX 1: Use environment variable for DEBUG. True for local, False for Render.
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = []
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')

if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Security and Host Settings
CSRF_TRUSTED_ORIGINS = [f'https://{RENDER_EXTERNAL_HOSTNAME}'] if RENDER_EXTERNAL_HOSTNAME else []

# Application definition

INSTALLED_APPS = [
    # Custom Apps
    'members',
    
    # Third-party Apps
    'crispy_forms',
    'crispy_bootstrap5',
    'whitenoise.runserver_nostatic', # Recommended for static file serving in development

    # --- Cloudinary & Storage Integration ---
    'cloudinary',
    'cloudinary_storage',

    # Django Built-in Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise is correctly placed here for serving static files
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'party_management.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'party_management.wsgi.application'


# Database Configuration (Defaults to PostgreSQL locally)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'party_db',
        'USER': 'party_user',
        # !!! WARNING: Never commit actual passwords. Use .env files locally.
        'PASSWORD': 'Wondej@2139', 
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# PRODUCTION/RENDER DATABASE CONFIGURATION (Overrides local settings)
# This will pull the database URL from the DATABASE_URL environment variable (used by Render)
DB_FROM_ENV = dj_database_url.config(conn_max_age=600)
DATABASES['default'].update(DB_FROM_ENV)


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
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


# =========================================================================
# --- Static Files (CSS, JavaScript, Images) Configuration (WhiteNoise) ---
# =========================================================================

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# FIX 2: Static files will be collected here for WhiteNoise to serve.
STATIC_ROOT = BASE_DIR / 'staticfiles'

# FIX 3: Configure WhiteNoise to serve and compress static files.
# Correction: This must be uncommented for WhiteNoise to work in production
# STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# =========================================================================
# --- Media Files (User Uploads) Configuration (Cloudinary/Local) ---
# =========================================================================

MEDIA_URL = '/media/'

# Cloudinary Configuration (Requires Environment Variables)
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')

# Conditional File Storage
if CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET:
    # Use Cloudinary for Media Storage in Production/Deployment
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    MEDIA_ROOT = None # Not needed when using a remote storage service
else:
    # Use local file storage in development
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    MEDIA_ROOT = BASE_DIR / 'media'
    # Ensure the 'media' directory exists locally
    os.makedirs(MEDIA_ROOT, exist_ok=True)


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication Settings
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'login_redirect'


# =========================================================================
# --- Email Configuration (Development vs. Production) ---
# =========================================================================

# settings.py

if 'RENDER' in os.environ:
    # --- PRODUCTION EMAIL SETTINGS (BREVO) ---
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp-relay.brevo.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.environ.get('BREVO_LOGIN_EMAIL')
    EMAIL_HOST_PASSWORD = os.environ.get('BREVO_SMTP_KEY')
    DEFAULT_FROM_EMAIL = EMAIL_HOST_USER # Brevo requires the from_email to be the login email
else:
    # --- DEVELOPMENT SETTINGS ---
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = 'development@example.com'
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

# Crispy Forms Settings
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
