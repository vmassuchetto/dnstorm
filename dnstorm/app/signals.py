from django.conf import settings
from django.db.models import signals
from django.utils.translation import ugettext_noop as _
from django.contrib.auth import login

from registration.signals import user_registered
from notification import models as notification
from actstream.actions import follow

from dnstorm.app.models import Invitation

def login_on_registration(sender, user, request, **kwargs):
    """
    Logs in the user after registration.
    """
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)

user_registered.connect(login_on_registration)

def create_notice_types(app, created_models, verbosity, **kwargs):
    """
    Register notification types for django-notification.
    """
    notification.create_notice_type(
        'invitation',
        _('Invitation received'),
        _('you have received an invitation to collaborate in problem'))

signals.post_syncdb.connect(create_notice_types, sender=notification)
