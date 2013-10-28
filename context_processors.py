from django.contrib.auth.forms import AuthenticationForm
from forms import AccountCreateForm

def base(request):
    context = dict()
    context['login_form'] = AuthenticationForm()
    context['register_form'] = AccountCreateForm()
    return context
