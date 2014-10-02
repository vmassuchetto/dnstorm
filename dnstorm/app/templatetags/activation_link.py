from django import template
from django.core.urlresolvers import reverse

from dnstorm.app.models import Invitation
from dnstorm.app.utils import get_object_or_none, get_option

register = template.Library()

def activation_link(invitation_id):
    invitation = get_object_or_none(Invitation, id=invitation_id)
    if not invitation:
        return ''
    return '%s%s?hash=%s' % (get_option('site_url'), reverse('registration_register'), invitation.hash)

register.simple_tag(activation_link)
