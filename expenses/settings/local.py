import locale, os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'yhrek_prod',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': 'yhrek_prod',
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': 'mysql',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '3306'                   # Set to empty string for default.
    }
}

SECRET_KEY=os.getenv('SECRET_KEY')
ROOT_URLCONF = 'expenses.urls'

EMAIL_HOST = os.getenv('EMAIL_HOST')
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
