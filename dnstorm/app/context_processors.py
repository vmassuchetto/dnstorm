from django.core.urlresolvers import reverse

from dnstorm.app.models import Option
from dnstorm.app import DNSTORM_URL

def base(request):
    context = dict()
    context['dnstorm_url'] = DNSTORM_URL
    context['options'] = Option().get_all()
    context['login_url'] = reverse('login') + '?next=' + request.build_absolute_uri()
    context['logout_url'] = reverse('logout') + '?next=' + request.build_absolute_uri()
    return context
