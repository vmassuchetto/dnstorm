from django.conf import settings
from django.db.models import signals
from django.utils.translation import ugettext_noop as _
from django.contrib.auth import login, authenticate

from registration.signals import user_activated
from notification import models as notification
from actstream.actions import follow

from dnstorm.app.models import Invitation

def register_invitations(sender, user, request, **kwarg):
    """
    Add user as a prooblem contributors on account activation according to
    pending invitations.
    """
    for i in Invitation.objects.filter(email=user.email):
        i.problem.contributor.add(user)
        follow(user, i.problem)
        notification.send([user], 'contributor', { 'from_user': i.problem.author, 'problem': i.problem })
        i.delete()

user_activated.connect(register_invitations)

def login_on_activation(sender, user, request, **kwargs):
    """
    Logs in the user after account activation.
    """
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)

user_activated.connect(login_on_activation)

def create_notice_types(app, created_models, verbosity, **kwargs):
    """
    Register notification types for django-notification.
    """
    notification.create_notice_type(
        'invitation',
        _('invitation received for a problem'),
        _('you have received an invitation to collaborate in problem'))
    notification.create_notice_type(
        'contributor',
        _('you were added as a contributor in a problem'),
        _('you have been added as a contributor of a problem'))

signals.post_syncdb.connect(create_notice_types, sender=notification)
