import os
import dj_database_url

from django.conf import global_settings

DEBUG = os.environ.get('DEBUG', False)
TEMPLATE_DEBUG = DEBUG

# Databases

if DEBUG:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'dnstorm.sqlite3',
            'ATOMIC_REQUESTS': True
        }
    }
else :
    DATABASES = { 'default': dj_database_url.config() }

# Other Django settings

ADMINS = (
    ('Vinicius Massuchetto', 'vmassuchetto@gmail.com'),
)

MANAGERS = ADMINS

ALLOWED_HOSTS = ['*']

TIME_ZONE = 'America/Chicago'
LANGUAGE_CODE = 'pt-br'
LANGUAGES = (
  ('en', 'English'),
  ('pt-br', 'Brazilian Portuguese'),
)

SITE_ID = 1
USE_I18N = True
USE_L10N = True
USE_TZ = True

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))
MEDIA_ROOT = SITE_ROOT + '/media/'
MEDIA_URL = ''
STATIC_ROOT = 'static'
STATIC_URL = '/static/'

SECRET_KEY = '+=hz$82m0-sh@+=i64h-+i%8_3+m=w2(^hf2bnha+v&6)^-qd^'

MIDDLEWARE_CLASSES = global_settings.MIDDLEWARE_CLASSES + (
    'reversion.middleware.RevisionMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = global_settings.TEMPLATE_CONTEXT_PROCESSORS + (
    'dnstorm.app.context_processors.base',
)

ROOT_URLCONF = 'dnstorm.app.urls'
LOGIN_REDIRECT_URL = '/'
WSGI_APPLICATION = 'dnstorm.wsgi.application'

# Apps

INSTALLED_APPS = (
    # Built-in apps included by default
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Built-in apps not included by default
    'django.contrib.humanize',

    # Third-party apps
    'avatar',
    'ckeditor',
    'crispy_forms',
    'crispy_forms_foundation',
    'haystack',
    'registration',
    'reversion',
    'south',

     # DNStorm app
    'dnstorm.app',
)

if DEBUG:
    INSTALLED_APPS = INSTALLED_APPS + ('debug_toolbar',)

# Logging

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
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

# Date formats

DATE_FORMAT = '%d %b %Y'
DATETIME_FORMAT = '%d %b %Y H:i'

# DNStorm settings

DNSTORM = {
    'table_prefix': 'dnstorm',
    'site_name': 'DNStorm',
    'site_description': 'An idea-generation platform',
    'site_language': 'en_EN',
}

# SMTP

EMAIL_HOST = False
EMAIL_PORT = False
EMAIL_HOST_USER = 'dnstorm@localhost'
EMAIL_HOST_PASSWORD = False

# CKEditor

CKEDITOR_DEFAULT_TOOLBAR = [
    ['Format'],
    ['Bold', 'Italic', 'Strike', '-', 'RemoveFormat'],
    ['NumberedList','BulletedList', 'Blockquote'],
    ['Link','Unlink','Anchor'],
    ['Image','Flash']
]
CKEDITOR_UPLOAD_PATH = SITE_ROOT
CKEDITOR_CONFIGS = {
    'default': { 'toolbar': CKEDITOR_DEFAULT_TOOLBAR },
    'idea_content': { 'toolbar': CKEDITOR_DEFAULT_TOOLBAR , 'height': 200 }
}

# Crispy Forms

TEMPLATE_PACK = 'foundation'
CRISPY_TEMPLATE_PACK = 'foundation'

# Haystack

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
    },
}
