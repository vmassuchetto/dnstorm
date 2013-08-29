from django.contrib.auth.forms import AuthenticationForm

def base(request):
    context = dict()
    context['login_form'] = AuthenticationForm()
    return context
