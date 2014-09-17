from django.core.urlresolvers import reverse

from actstream.models import user_stream

from dnstorm.app.models import Option
from dnstorm.app import DNSTORM_URL
from dnstorm.app.utils import get_option

def base(request):
    context = dict()
    context['dnstorm_url'] = DNSTORM_URL
    context['options'] = Option().get_all()
    context['login_url'] = reverse('login') + '?next=' + request.build_absolute_uri()
    context['logout_url'] = reverse('logout') + '?next=' + request.build_absolute_uri()
    context['user_activity'] = user_stream(request.user) if request.user.is_authenticated() else None
    context['user_activity_counter'] = get_option('user_%d_activity_counter' % request.user.id) if request.user.is_authenticated else None
    return context
