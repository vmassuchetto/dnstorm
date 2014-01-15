from django.contrib.auth.forms import AuthenticationForm
from dnstorm.app.models import Option
from dnstorm.app import DNSTORM_URL

def base(request):
    context = dict()
    context['dnstorm_url'] = DNSTORM_URL
    context['options'] = Option().get_all()
    if not request.user.is_authenticated():
        context['login_form'] = AuthenticationForm()
    return context
