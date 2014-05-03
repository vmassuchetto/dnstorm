from defaults import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'dnstorm.sqlite3',
        'ATOMIC_REQUESTS': True
    }
}

ADMINS = (
    ('Django Dev', 'django@localhost'),
)
MANAGERS = ADMINS

DEBUG = True
TEMPLATE_DEBUG = DEBUG

INSTALLED_APPS = INSTALLED_APPS + ('debug_toolbar',)

TIME_ZONE = 'America/Sao_Paulo'
LANGUAGE_CODE = 'pt-br'

SECRET_KEY = '+=hz$82m0-sh@+=i64h-+i%8_3+m=w2(^hf2bnha+v&6)^-qd^'

RECAPTCHA_PUBLIC_KEY = '6LdLIvISAAAAAP0o3HsmY0rn-SIz8i-U_nh4HQIA'
RECAPTCHA_PRIVATE_KEY = '6LdLIvISAAAAACQHjNC_OYr9am6khQEOOSqxoqek'

AJAX_SELECT_BOOTSTRAP = False