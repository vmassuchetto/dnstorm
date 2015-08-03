from defaults import *
import dj_database_url

DATABASES = { 'default': dj_database_url.config() }

ADMINS = (
    ('Vinicius Massuchetto', 'vmassuchetto@gmail.com'),
)

PRODUCTION = True
DEBUG = True
TEMPLATE_DEBUG = DEBUG

COMPRESS_ENABLED = False

TIME_ZONE = 'America/Sao_Paulo'
LANGUAGE_CODE = 'pt-br'

SECRET_KEY = 'YOUR_SECRET_KEY'

DEFAULT_FROM_EMAIL = 'emailaddress@email.com'
SERVER_EMAIL = 'emailaddress@email.com'
EMAIL_HOST = 'smtp.host.com'
EMAIL_HOST_USER = 'emailaddress@email.com'
EMAIL_HOST_PASSWORD = 'password'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
