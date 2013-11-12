from django.contrib.auth.forms import AuthenticationForm
from forms import AccountCreateForm

def base(request):
    context = dict()
    if not request.user.is_authenticated():
        context['login_form'] = AuthenticationForm()
    return context
