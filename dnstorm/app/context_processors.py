from django.contrib.auth.forms import AuthenticationForm
from django.core.urlresolvers import reverse

from actstream.models import user_stream

from dnstorm.app import DNSTORM_URL
from dnstorm.app.utils import get_option
from dnstorm.app.models import Problem, Idea
from dnstorm.app.utils import get_option

def base(request):
    """
    Provides basic variables used for all templates.
    """
    context = dict()
    context['dnstorm_url'] = DNSTORM_URL

    # Links
    if not context.get('site_title', None):
        context['site_title'] = '%s | %s' % (
            get_option('site_title'), get_option('site_description'))
    context['site_url'] = get_option('site_url')
    context['login_form'] = AuthenticationForm()
    context['login_url'] = reverse('login') + '?next=' + request.build_absolute_uri() if 'next' not in request.GET else ''
    context['logout_url'] = reverse('logout') + '?next=' + request.build_absolute_uri() if 'next' not in request.GET else ''

    # Checks
    context['is_update'] = 'update' in request.resolver_match.url_name

    # Activity
    context['user_activity'] = user_stream(request.user, with_user_activity=False) if request.user.is_authenticated() else None
    context['user_activity_counter'] = get_option('user_%d_activity_counter' % request.user.id) if request.user.is_authenticated() else None

    return context
