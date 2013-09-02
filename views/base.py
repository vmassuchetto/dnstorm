from django.contrib.auth.models import User
from django.views.generic import DetailView
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.http import Http404
from django.utils.translation import ugettext as _

from dnstorm.models import Problem
from dnstorm.forms import OptionsForm

class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, *args, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['problems'] = Problem.objects.all()
        return context

class OptionsView(FormView):
    template_name = 'options.html'
    form_class = OptionsForm

class ProfileView(DetailView):
    template_name = 'profile.html'
    model = User

    def get_context_data(self, *args, **kwargs):
        context = super(ProfileView, self).get_context_data(**kwargs)
        try:
            context['user'] = User.objects.get(username=kwargs['username'])
        except User.DoesNotExist:
            raise Http404
        return context
