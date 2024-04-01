# Django settings for expenses project.

import os
import sys
import locale
from django.utils.translation import gettext_lazy as _

PROJECT_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(__file__).replace('settings', ''), ''))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "apps"))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# VAIHDA muuttujat .env tiedostoon juureen
api_key = os.getenv('SENDGRID_API_KEY')
# Python vaatii tekstin converttauksen booleaniksi toimiakseen
DEBUG = os.getenv('DEBUG') == 'True'
ALLOWED_HOSTS = list(os.getenv('ALLOWED_HOSTS_STRING').split(','))
SECRET_KEY = os.getenv('SECRET_KEY')

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
TEMPLATE_DEBUG = DEBUG
locale.setlocale(locale.LC_ALL, 'fi_FI.UTF-8')

# 2.5MB - 2621440
# 5MB - 5242880
# 10MB - 10485760
# 16MB - 16777216
# 20MB - 20971520
# 50MB - 5242880
# 100MB 104857600
# 250MB - 214958080
# 500MB - 429916160
MAX_UPLOAD_SIZE = 20971520
# VAIHDA Admin (Nimi, email) halutuksi. Virheilmoitukset lähetetään sähköpostiin.)
ADMINS = (
    ('Webmaster', 'hostmaster@yhrek.fi'),
)

MANAGERS = ADMINS


DATABASES = {
    'default': {
        # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'ENGINE': 'django.db.backends.postgresql',
        # Or path to database file if using sqlite3.
        'NAME': 'postgres',
        # The following settings are not used with sqlite3:
        'USER': 'postgres',
        # 'PASSWORD': '',
        # Docker-composesta viittaus
        # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'HOST': 'db',
        'PORT': '5432',                      # Set to empty string for default.
    }
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Europe/Helsinki'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'fi-FI'
#LANGUAGE_CODE = 'fi'

LANGUAGES = (
    ('fi-FI', _('Finnish')),
    ('sv-SE', _('Swedish')),
    ('en-EN', _('English')),
)

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = '/media/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
#STATIC_ROOT = os.path.join(BASE_DIR, 'expenses/static')
STATIC_ROOT = '/code/static/'

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

LOGIN_REDIRECT_URL = '/expense/'
LOGOUT_REDIRECT_URL = '/accounts/login/'


MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.RemoteUserMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'crum.CurrentRequestUserMiddleware',
    'django.middleware.common.BrokenLinkEmailsMiddleware'
]
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # insert your TEMPLATE_DIRS here
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'expenseapp.context_processors.infobanner_processor.info_message'
            ],
        },
    },
]

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'expenseapp.middleware.setlanguage.ExpenseAppSetLanguageMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'expenses.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'expenses.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'localflavor',
    'expenseapp',
    'django.contrib.admin',
    'django_registration',
    'django.contrib.flatpages',
)

ACCOUNT_ACTIVATION_DAYS = 14

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django.security.DisallowedHost': {
            'handlers': ['null'],
            'propagate': False,
        },
    }
}

EMAIL_SUBJECT_PREFIX = '[Kululasku] '

try:
    from .local import *
except ImportError:
  pass

#VAIHDA
DEFAULT_FROM_EMAIL="no-reply@yhrek.fi"
import locale, os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': os.getenv('MYSQL_NAME'),                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': os.getenv('MYSQL_USER'),
        'PASSWORD': os.getenv('MYSQL_PASSWORD'),
        'HOST': os.getenv('MYSQL_HOST'),                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '3306'                   # Set to empty string for default.
    }
}

SECRET_KEY=os.getenv('SECRET_KEY')

EMAIL_HOST = os.getenv('SMTP_HOST')
EMAIL_HOST_USER = os.getenv('SMTP_USER')
EMAIL_HOST_PASSWORD = os.getenv('SMTP_PASSWORD')
EMAIL_PORT = os.getenv('SMTP_PORT')
EMAIL_USE_TLS = True
locale.setlocale(locale.LC_ALL, 'fi_FI.UTF-8')

#locale.setlocale(locale.LC_ALL, 'fi_FI')

LOGGING = {
  'version': 1,
  'disable_existing_loggers': False,
  'handlers': {
    'null': {
      'level': 'DEBUG',
      'class': 'logging.NullHandler',
    },
  },
  'loggers': {
    'django.security.DisallowedHost': {
      'handlers': ['null'],
      'propagate': False,
    },
  },
}
