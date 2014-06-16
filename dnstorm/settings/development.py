from defaults import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'dnstorm.sqlite3',
        'ATOMIC_REQUESTS': False
    }
}

ADMINS = (
    ('Django Dev', 'django@localhost'),
)
MANAGERS = ADMINS

PRODUCTION = False
DEBUG = True
TEMPLATE_DEBUG = DEBUG

COMPRESS_PRECOMPILERS = (
    ('text/x-sass', 'sass --compass "{infile}" "{outfile}"'),
    ('text/x-scss', 'sass --scss --compass -I "%s/bower_components/foundation/scss" "{infile}" "{outfile}"' % BOWER_COMPONENTS_ROOT),
)

COMPRESS_ENABLED = True
COMPRESS_ROOT = SITE_ROOT + '/app/static/'
COMPRESS_URL = '/static/'
COMPRESS_OUTPUT_DIR = ''

INSTALLED_APPS = INSTALLED_APPS + ('debug_toolbar',)

TIME_ZONE = 'America/Sao_Paulo'
LANGUAGE_CODE = 'pt-br'

SECRET_KEY = '+=hz$82m0-sh@+=i64h-+i%8_3+m=w2(^hf2bnha+v&6)^-qd^'
