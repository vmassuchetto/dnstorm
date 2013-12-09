from django.contrib.auth.forms import AuthenticationForm
from dnstorm.forms import AccountCreateForm
from dnstorm.models import Option

def base(request):
    context = dict()
    option = Option()
    context['options'] = option.get_all()
    if not request.user.is_authenticated():
        context['login_form'] = AuthenticationForm()
    return context
