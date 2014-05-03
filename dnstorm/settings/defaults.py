import os

from django.conf import global_settings

ALLOWED_HOSTS = ['*']

LANGUAGES = (
    ('en', 'English'),
    ('pt-br', 'Brazilian Portuguese'),
)

SITE_ID = 1
USE_I18N = True
USE_L10N = True
USE_TZ = True

SITE_ROOT = os.path.dirname(os.path.realpath(__file__)) + '/../'
MEDIA_ROOT = SITE_ROOT + '/media/'
MEDIA_URL = ''
STATIC_ROOT = 'static'
STATIC_URL = '/static/'

MIDDLEWARE_CLASSES = global_settings.MIDDLEWARE_CLASSES + (
    'reversion.middleware.RevisionMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = global_settings.TEMPLATE_CONTEXT_PROCESSORS + (
    'django.core.context_processors.request',
    'dnstorm.app.context_processors.base',
)

ROOT_URLCONF = 'dnstorm.app.urls'
LOGIN_REDIRECT_URL = '/'
WSGI_APPLICATION = 'dnstorm.wsgi.application'
AVATAR_GRAVATAR_DEFAULT = 'identicon'

# Apps

INSTALLED_APPS = (

    # Django apps
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # Required apps for DNStorm
    'avatar',
    'ajax_select',
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

AJAX_LOOKUP_CHANNELS = {
    'user': ('dnstorm.app.lookups', 'UserLookup')
}

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

# Registration

ACCOUNT_ACTIVATION_DAYS = 3

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