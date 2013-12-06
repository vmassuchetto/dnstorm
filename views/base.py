from django.contrib.auth.models import User
from django.views.generic import DetailView
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator

from dnstorm.models import Problem
from dnstorm.forms import OptionsForm, AccountCreateForm

class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, *args, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        problems = Paginator(Problem.objects.all(), 25)
        page = self.request.GET['page'] if 'page' in self.request.GET else 1
        context['problems'] = problems.page(page)
        context['problems_total'] = Problem.objects.all().count()
        return context

class OptionsView(FormView):
    template_name = 'options.html'
    form_class = OptionsForm

    def get_context_data(self, *args, **kwargs):
        context = super(OptionsView, self).get_context_data(**kwargs)
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['title'] = _('Options')
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Options'), 'classes': 'current' } ]

class UserView(TemplateView):
    template_name = 'user.html'

    def get_context_data(self, *args, **kwargs):
        context = super(UserView, self).get_context_data(**kwargs)
        self.user = get_object_or_404(User, username=kwargs['username'])
        context['breadcrumbs'] = self.get_breadcrumbs()
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Users'), 'classes': 'unavailable' },
            { 'title': self.user.username, 'classes': 'current' } ]
