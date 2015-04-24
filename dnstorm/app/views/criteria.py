import random

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_protect
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from dnstorm.app import permissions
from dnstorm.app.forms import CriteriaForm
from dnstorm.app.models import Criteria, Problem
from dnstorm.app.utils import get_object_or_none, activity_count, get_option, activity_register
from dnstorm.app.views.problem import problem_buttons

class CriteriaCreateView(CreateView):
    template_name = '_update_criteria.html'
    form_class = CriteriaForm
    model = Criteria

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        self.problem = get_object_or_404(Problem, id=kwargs['problem'])
        if not permissions.problem(obj=self.problem, user=self.request.user, mode='edit'):
            raise PermissionDenied
        return super(CriteriaCreateView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(CriteriaCreateView, self).get_context_data(**kwargs)
        context['site_title'] = '%s' % (_('Create criteria'))
        context['info'] = self.get_info()
        context['title'] = _('Create criteria for problem: %s' % self.problem.title)
        return context

    def get_info(self):
        return {
            'icon': 'pencil',
            'icon_url': reverse('problem_tab_criteria', kwargs={'pk': self.problem.id, 'slug': self.problem.slug}),
            'title': _('Create criteria'),
            'title_url': self.problem.get_absolute_url(),
            'buttons': problem_buttons(self.request, self.problem),
            'show': permissions.problem(obj=self.problem, user=self.request.user, mode='edit')
        }

    def form_valid(self, form):
        form.instance.problem = self.problem
        form.instance.author = self.request.user
        form.instance.save()
        messages.success(self.request, mark_safe(_('Criteria created.')))
        activity_register(self.request.user, form.instance)
        return HttpResponseRedirect(reverse('problem_tab_criteria', kwargs={'pk': self.problem.id, 'slug': self.problem.slug}))

class CriteriaDeleteView(DeleteView):
    model = Criteria

    @method_decorator(login_required)
    def get_object(self, *args, **kwargs):
        criteria = get_object_or_404(Criteria, id=kwargs['pk'])
        if not permissions.criteria(obj=criteria, user=self.request.user, mode='manage'):
            raise PermissionDenied
        return criteria

class CriteriaUpdateView(UpdateView):
    template_name = '_update_criteria.html'
    form_class = CriteriaForm
    model = Criteria

    @method_decorator(login_required)
    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        self.object = get_object_or_404(Criteria, id=kwargs['pk'])
        self.problem = self.object.problem
        if not permissions.criteria(obj=self.object, user=self.request.user, mode='manage'):
            raise PermissionDenied
        return super(CriteriaUpdateView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(CriteriaUpdateView, self).get_context_data(**kwargs)
        context['site_title'] = '%s | %s' % (self.object.name, _('Edit criteria'))
        context['info'] = self.get_info()
        context['title'] = _('Edit criteria for problem: %s' % self.problem.title)
        return context

    def form_valid(self, form):
        form.instance.save()
        messages.success(self.request, mark_safe(_('Criteria saved.')))
        activity_register(self.request.user, form.instance)
        return HttpResponseRedirect(reverse('problem_tab_criteria', kwargs={'pk': self.problem.id, 'slug': self.problem.slug}))

    def get_info(self):
        return {
            'icon': 'pencil',
            'icon_url': reverse('problem', kwargs={'pk': self.problem.id, 'slug': self.problem.slug}),
            'title': _('Edit criteria'),
            'title_url': self.object.get_absolute_url(),
            'buttons': problem_buttons(self.request, self.problem),
            'show': permissions.problem(obj=self.problem, user=self.request.user, mode='edit')
        }
