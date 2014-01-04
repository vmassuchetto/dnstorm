# Django settings for dnstorm project.
import os
import dj_database_url

LOCALENV = False

ADMINS = (
    ('Vinicius Massuchetto', 'vmassuchetto@gmail.com'),
)

MANAGERS = ADMINS

if LOCALENV:
    DEBUG = True
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'dnstorm.sqlite3'
        }
    }
else :
    DEBUG = False
    DATABASES = { 'default': dj_database_url.config() }

TEMPLATE_DEBUG = DEBUG

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['*']

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'pt-br'
LANGUAGES = (
  ('en', 'English'),
  ('pt-br', 'Brazilian Portuguese'),
)

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = SITE_ROOT + '/media/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = 'static'

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

# Make this unique, and don't share it with anybody.
SECRET_KEY = '+=hz$82m0-sh@+=i64h-+i%8_3+m=w2(^hf2bnha+v&6)^-qd^'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'reversion.middleware.RevisionMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.request',
    'absolute.context_processors.absolute',
    'dnstorm.app.context_processors.base'
)

ROOT_URLCONF = 'dnstorm.app.urls'
LOGIN_REDIRECT_URL = '/'
# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'dnstorm.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

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
    'absolute',
    'ckeditor',
    'crispy_forms',
    'crispy_forms_foundation',
    'gravatar',
    'registration',
    'reversion',
    'south',

     # DNStorm app
    'dnstorm.app',
)

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

# DNStorm

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