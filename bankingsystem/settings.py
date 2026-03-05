
import os
from pathlib import Path
import cloudinary
import cloudinary.uploader
import cloudinary.api
#import #django_heroku
import dj_database_url

from django.contrib.messages import constants as messages
import os
import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = Path(__file__).resolve().parent.parent
CSRF_TRUSTED_ORIGINS = [
    "https://web-production-6420a.up.railway.app",
    "https://www.san-tandorglobal.online"
]

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ')_z--t-qq1=s!l*c-1pg(%$3l%=ys9m7!fh@jtom47ozn-24^*'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'admin_soft.apps.AdminSoftDashboardConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',


 
    'accounts',
    'ip_ban',    
    'core',
    'transactions',
    'bankcard',
    'corsheaders',
    'storages'
]



MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'ip_ban.middleware.IPBanMiddleware',

    "corsheaders.middleware.CorsMiddleware",

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'accounts.middleware.AccountRestrictionMiddleware',  # Add this line

    
]

AUTH_USER_MODEL = 'accounts.User'

LOGIN_URL = "/accounts/login/"

ROOT_URLCONF = 'bankingsystem.urls'

# settings.py addition - add these settings to your settings.py
IP_BAN_SETTINGS = {
    'SAFE_IPS': [
        '127.0.0.1',
        'localhost',
        '::1',
    ],
    'SAFE_PATHS': [
        '/staff/',
        '/admin/',
        '/staff/login/',
        '/admin/login/',
    ]
}
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates'
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

WSGI_APPLICATION = 'bankingsystem.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases



DATABASE_URL = "postgresql://neondb_owner:npg_6LIMten5JUdK@ep-floral-bonus-aduqxvhy-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

# Configure the default database using the DATABASE_URL
DATABASES = {
    'default': dj_database_url.config(default=DATABASE_URL)
}
"""

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

"""
# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 4,  # Change this to your desired minimum password length
        },
    },
]

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]
STATICSTORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


MESSAGE_TAGS = {
    messages.SUCCESS: 'alert-success',
    messages.ERROR: 'alert-danger',
}

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'accounts.backends.AccountNoBackend',
    'accounts.backends.CustomAuthBackend',
)



#django_heroku.settings(locals())


DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'          
cloudinary.config( 
  cloud_name = "dcgbuogjb", 
  api_key = "979861478794234", 
  api_secret = "oVnYxXqlEG9xM0t4X-j3CIE5Hz4" 
)

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'






EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.zoho.com'
EMAIL_PORT = 465  # Correct port for SSL
EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'support@san-tandorglobal.online'
EMAIL_HOST_PASSWORD = '4Support51a5113$'
DEFAULT_FROM_EMAIL = 'support@san-tandorglobal.online'
