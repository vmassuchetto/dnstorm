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
from django.utils.safestring import mark_safe

from dnstorm.app import models
from dnstorm.app import forms

class CriteriaListView(TemplateView):
    template_name = 'criteria_list.html'
    model = models.Criteria

    def get_context_data(self, *args, **kwargs):
        context = super(CriteriaListView, self).get_context_data(**kwargs)
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['sidebar'] = True
        criterias = Paginator(models.Criteria.objects.all().order_by('name'), 25)
        page = self.request.GET['page'] if 'page' in self.request.GET else 1
        context['criterias'] = criterias.page(page)
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Criterias'), 'classes': 'current' } ]

class CriteriaView(TemplateView):
    template_name = 'criteria.html'
    model = models.Criteria

    def dispatch(self, request, *args, **kwargs):
        self.criteria = get_object_or_404(models.Criteria, slug=kwargs['slug'])
        return super(CriteriaView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(CriteriaView, self).get_context_data(**kwargs)

        star = '<i class="fi-star"></i>'
        self.criteria.stars = list()
        for i in range(1,6):
            self.criteria.stars.append({
                'icons': mark_safe(star * i),
                'help': getattr(self.criteria, 'help_star%d' % i)
            })

        context['breadcrumbs'] = self.get_breadcrumbs()
        context['sidebar'] = True
        context['title'] = self.criteria.name
        context['criteria'] = self.criteria
        problems = Paginator(models.Problem.objects.filter(criteria=self.criteria).order_by('-created'), 25)
        page = self.request.GET['page'] if 'page' in self.request.GET else 1
        context['problems'] = problems.page(page)
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Criterias'), 'url': reverse('criteria_list') },
            { 'title': self.criteria.name, 'url': self.criteria.get_absolute_url(), 'classes': 'current' } ]

class CriteriaCreateView(CreateView):
    template_name = 'criteria_edit.html'
    form_class = forms.CriteriaForm
    model = models.Criteria

    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        return super(CriteriaCreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(CriteriaCreateView, self).get_context_data(**kwargs)
        context['breadcrumbs'] = self.get_breadcrumbs()
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Criterias'), 'url': reverse('criteria_list') },
            { 'title': _('Create'), 'classes': 'current' } ]

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, _('Criteria created.'))
        return HttpResponseRedirect(reverse('criteria', kwargs={'slug': self.object.slug}))

class CriteriaUpdateView(UpdateView):
    template_name = 'criteria_edit.html'
    form_class = forms.CriteriaForm
    model = models.Criteria

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
            { 'title': _('Criterias'), 'url': reverse('criteria_list') },
            { 'title': self.object.name, 'url': self.object.get_absolute_url() },
            { 'title': _('Edit'), 'classes': 'current' } ]

    def form_valid(self, form):
        self.object.save()
        messages.success(self.request, _('Criteria saved.'))
        return HttpResponseRedirect(reverse('criteria', kwargs={'slug': self.object.slug}))
