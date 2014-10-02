from django.core.urlresolvers import reverse

from actstream.models import user_stream

from dnstorm.app import DNSTORM_URL
from dnstorm.app.utils import get_option

def base(request):
    context = dict()
    context['dnstorm_url'] = DNSTORM_URL
    context['site_title'] = '%s | %s' % (get_option('site_title'), get_option('site_description'))
    context['site_url'] = get_option('site_url')
    context['login_url'] = reverse('login') + '?next=' + request.build_absolute_uri()
    context['logout_url'] = reverse('logout') + '?next=' + request.build_absolute_uri()
    context['user_activity'] = user_stream(request.user)[:15] if request.user.is_authenticated() else None
    context['user_activity_counter'] = get_option('user_%d_activity_counter' % request.user.id) if request.user.is_authenticated() else None
    return context
