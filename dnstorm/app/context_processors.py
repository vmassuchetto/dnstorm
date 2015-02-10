from django.core.urlresolvers import reverse

from actstream.models import user_stream

from dnstorm.app import DNSTORM_URL
from dnstorm.app.utils import get_option
from dnstorm.app.models import Problem, Idea

def base(request):
    """
    Provides basic variables used for all templates.
    """
    context = dict()
    context['dnstorm_url'] = DNSTORM_URL

    # Drafts
    if request.user.is_authenticated():
        context['problem_drafts'] = Problem.objects.filter(published=False, author=request.user)
        context['idea_drafts'] = Idea.objects.filter(published=False, author=request.user)
        context['drafts_count'] = len(context['problem_drafts']) + len(context['idea_drafts'])
    else:
        context['problem_drafts'] = False
        context['idea_drafts'] = False
        context['drafts_count'] = 0

    # Links
    context['site_title'] = '%s | %s' % (get_option('site_title'), get_option('site_description'))
    context['site_url'] = get_option('site_url')
    context['login_url'] = reverse('login') + '?next=' + request.build_absolute_uri() if 'next' not in request.GET else ''
    context['logout_url'] = reverse('logout') + '?next=' + request.build_absolute_uri() if 'next' not in request.GET else ''

    # Activity
    context['user_activity'] = user_stream(request.user)[:15] if request.user.is_authenticated() else None
    context['user_activity_counter'] = get_option('user_%d_activity_counter' % request.user.id) if request.user.is_authenticated() else None

    return context
