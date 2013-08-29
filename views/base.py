from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.utils.translation import ugettext as _

from dnstorm.models import Problem
from dnstorm.forms import OptionsForm

class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, *args, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['problems'] = Problem.objects.filter(revision=None)[:10]
        return context

class OptionsView(FormView):
    template_name = 'options.html'
    form_class = OptionsForm

class ErrorView(TemplateView):
    template_name = 'error.html'

    def get_context_data(self, *args, **kwargs):
        context = super(ErrorView, self).get_context_data(**kwargs)
        if self.kwargs['type'] == 'permission':
            context['message'] = _('You don\'t have permission to access the page you requested.')
        elif self.kwargs['type'] == 'not_exists':
            context['message'] = _('The object you are trying to access does not exist.')
        else:
            context['message'] = _('There was an error during the request.')
        return context
