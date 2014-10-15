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
from dnstorm.app import permissions
from dnstorm.app.utils import get_option


class CriteriasView(TemplateView):
    template_name = 'criteria.html'

    def get_context_data(self, *args, **kwargs):
        context = super(CriteriasView, self).get_context_data(**kwargs)
        criterias = Paginator(models.Criteria.objects.filter(author=self.request.user).order_by('name'), 20)
        context['site_title'] = '%s | %s' % (_('Criterias'), get_option('site_title'))
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['criterias'] = criterias.page(self.request.GET.get('page', 1))
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Criterias'), 'classes': 'current' }
        ]

class CriteriaCreateView(CreateView):
    template_name = 'criteria_update.html'
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
            { 'title': _('Criterias'), 'url': reverse('criteria') },
            { 'title': _('Create'), 'classes': 'current' } ]

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, _('Criteria created.'))
        return HttpResponseRedirect(reverse('criteria', kwargs={'slug': self.object.slug}))

class CriteriaUpdateView(UpdateView):
    template_name = 'criteria_update.html'
    form_class = forms.CriteriaForm
    model = models.Criteria

    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        self.object = get_object_or_404(models.Criteria, slug=kwargs['slug'])
        if not permissions.criteria(obj=self.object, user=self.request.user, mode='manage'):
            raise PermissionDenied
        return super(CriteriaUpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(CriteriaUpdateView, self).get_context_data(**kwargs)
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['criteria'] = self.object
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Criterias'), 'url': reverse('criterias') },
            { 'title': self.object.name, 'url': self.object.get_absolute_url() },
            { 'title': _('Edit'), 'classes': 'current' } ]

    def form_valid(self, form):
        self.object.save()
        messages.success(self.request, _('Criteria saved.'))
        return HttpResponseRedirect(reverse('criterias'))
