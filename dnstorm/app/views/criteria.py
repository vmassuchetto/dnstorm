from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages

import reversion

from dnstorm.app.models import Problem, Criteria, ActivityManager
from dnstorm.app.forms import CriteriaForm

class CriteriaListView(TemplateView):
    template_name = 'criteria.html'
    model = Criteria

    def get_context_data(self, *args, **kwargs):
        context = super(CriteriaListView, self).get_context_data(**kwargs)
        context['breadcrumbs'] = self.get_breadcrumbs()
        criterias = Paginator(Criteria.objects.all().order_by('name'), 25)
        page = self.request.GET['page'] if 'page' in self.request.GET else 1
        context['criterias'] = criterias.page(page)
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Problems'), 'url': reverse('home') },
            { 'title': _('Criterias'), 'classes': 'current' } ]

class CriteriaProblemView(TemplateView):
    template_name = 'home.html'

    def dispatch(self, request, *args, **kwargs):
        self.criteria = get_object_or_404(Criteria, slug=kwargs['slug'])
        return super(CriteriaProblemView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(CriteriaProblemView, self).get_context_data(**kwargs)
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['criteria'] = self.criteria
        problems = Paginator(Problem.objects.filter(criteria=self.criteria).order_by('-modified'), 25)
        page = self.request.GET['page'] if 'page' in self.request.GET else 1
        context['problems'] = problems.page(page)
        context['activities'] = ActivityManager().get_objects(limit=4)
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Problems'), 'url': reverse('home') },
            { 'title': _('Criterias'), 'url': reverse('criteria_list') },
            { 'title': self.criteria.name, 'url': self.criteria.get_absolute_url(), 'classes': 'current' } ]

class CriteriaCreateView(CreateView):
    template_name = 'criteria_edit.html'
    form_class = CriteriaForm
    model = Criteria

    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        return super(CriteriaCreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(CriteriaCreateView, self).get_context_data(**kwargs)
        context['breadcrumbs'] = self.get_breadcrumbs()
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Problems'), 'url': reverse('home') },
            { 'title': _('Criterias'), 'url': reverse('criteria_list') },
            { 'title': _('Create'), 'classes': 'current' } ]

    @reversion.create_revision()
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, _('Criteria created.'))
        return HttpResponseRedirect(reverse('criteria', kwargs={'slug': self.object.slug}))

class CriteriaUpdateView(UpdateView):
    template_name = 'criteria_edit.html'
    form_class = CriteriaForm
    model = Criteria

    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        return super(CriteriaUpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(CriteriaUpdateView, self).get_context_data(**kwargs)
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['criteria'] = self.object
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Problems'), 'url': reverse('home') },
            { 'title': _('Criterias'), 'url': reverse('criteria_list') },
            { 'title': self.object.name, 'url': self.object.get_absolute_url() },
            { 'title': _('Edit'), 'classes': 'current' } ]

    @reversion.create_revision()
    def form_valid(self, form):
        self.object.save()
        messages.success(self.request, _('Criteria saved.'))
        return HttpResponseRedirect(reverse('criteria', kwargs={'slug': self.object.slug}))
