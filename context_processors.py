from django.contrib.auth.forms import AuthenticationForm
from app.forms import AccountCreateForm
from app.models import Option
from app import DNSTORM_URL

def base(request):
    context = dict()
    option = Option()
    context['dnstorm_url'] = DNSTORM_URL
    context['options'] = option.get_all()
    if not request.user.is_authenticated():
        context['login_form'] = AuthenticationForm()
    return context
