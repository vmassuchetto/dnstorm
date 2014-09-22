from datetime import datetime
from lxml.html.diff import htmldiff
import bleach
import re
import time

from django.contrib import messages
from django.contrib.auth import get_user
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.db.models.query import EmptyQuerySet
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.utils.html import strip_tags
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_protect
from django.views.generic import DetailView
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView

from actstream import action
from actstream.actions import follow, is_following
from actstream.models import any_stream

from dnstorm import settings
from dnstorm.app import forms
from dnstorm.app import models
from dnstorm.app import permissions
from dnstorm.app.utils import get_object_or_none, activity_count, get_option
from dnstorm.app.views.idea import idea_save

def problem_save(obj, form):
    """
    Save the object, clear the criterias and add the submited ones in
    ``request.POST``. This method will be the same for ProblemCreateView and
    ProblemUpdateView.
    """

    obj.object = form.save(commit=False)

    # Remember if new

    new = False if hasattr(obj.object, 'id') and isinstance(obj.object.id, int) else True
    old_diffhtml = render_to_string('problem_diffbase.html', {'problem': get_object_or_404(models.Problem, id=obj.object.id)}) if not new else None

    # Save problem

    obj.object.author = obj.request.user
    obj.object.description = bleach.clean(obj.object.description,
        tags=settings.SANITIZER_ALLOWED_TAGS,
        attributes=settings.SANITIZER_ALLOWED_ATTRIBUTES,
        styles=settings.SANITIZER_ALLOWED_STYLES,
        strip=True, strip_comments=True)
    obj.object.save()

    obj.object.criteria.clear()
    criterias = [i for i in obj.request.POST.get('criteria', '').split('|') if i.isdigit()]
    for c in models.Criteria.objects.filter(id__in=criterias):
        obj.object.criteria.add(c)

    obj.object.save()

    # Get a content diff

    new_diffhtml = render_to_string('problem_diffbase.html', {'problem': obj.object})
    if not new:
        problemdiff = htmldiff(old_diffhtml, new_diffhtml)
    else:
        problemdiff = new_diffhtml

    # Follow and send an action for the problem

    follow(obj.object.author, obj.object, actor_only=False) if not is_following(obj.object.author, obj.object) else None
    a = action.send(obj.object.author, verb='created' if new else 'edited', action_object=obj.object)
    if problemdiff:
        a[0][1].data = {'diff': problemdiff}
        a[0][1].save()
    activity_count(obj.object)

    messages.success(obj.request, _('Problem saved'))
    return HttpResponseRedirect(reverse('problem', kwargs={'slug':obj.object.slug}))

class ProblemCreateView(CreateView):
    template_name = 'problem_edit.html'
    form_class = forms.ProblemForm
    model = models.Problem

    @method_decorator(login_required)
    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        return super(ProblemCreateView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(ProblemCreateView, self).get_context_data(**kwargs)
        context['site_title'] = '%s | %s' % (_('Create problem'), get_option('site_title'))
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['title'] = _('Create new problem')
        context['criteria_form'] = forms.CriteriaForm()
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Create new problem'), 'url': reverse('problem_new'), 'classes': 'current' } ]

    def form_valid(self, form):
        return problem_save(self, form)

class ProblemUpdateView(UpdateView):
    template_name = 'problem_edit.html'
    form_class = forms.ProblemForm
    model = models.Problem

    @method_decorator(login_required)
    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        obj = get_object_or_404(models.Problem, slug=kwargs['slug'])
        if not permissions.problem(obj=obj, user=self.request.user, mode='manage'):
            raise PermissionDenied
        return super(ProblemUpdateView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(ProblemUpdateView, self).get_context_data(**kwargs)
        context['site_title'] = '%s | %s' % (self.object.title, _('Edit'))
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['title'] = _('Edit problem')
        context['criteria_form'] = forms.CriteriaForm()
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': self.object.title, 'url': self.object.get_absolute_url() },
            { 'title': _('Update'), 'url': reverse('problem_edit', kwargs={'slug':self.object.slug}), 'classes': 'current' } ]

    def form_valid(self, form):
        return problem_save(self, form)

class ProblemDeleteView(RedirectView):
    model = models.Problem
    success_url = '/'

    def dispatch(self, *args, **kwargs):
        obj = get_object_or_404(Problem, slug=kwargs['slug'])
        if not permissions.problem(obj=obj, user=self.request.user, mode='contribute'):
            raise PermissionDenied
        if len(self.request.POST) > 0:
            messages.success(self.request, _('Problem deleted'))
        return super(ProblemDeleteView, self).dispatch(*args, **kwargs)

class ProblemView(FormView):
    template_name = 'problem.html'
    form_class = forms.IdeaForm

    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        self.problem = get_object_or_404(models.Problem, slug=self.kwargs['slug'])
        if not permissions.problem(obj=self.problem, user=self.request.user, mode='view'):
            raise PermissionDenied
        return super(ProblemView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(ProblemView, self).get_form_kwargs()
        kwargs['problem'] = self.problem
        return kwargs

    def get_context_data(self, *args, **kwargs):
        context = super(ProblemView, self).get_context_data(**kwargs)
        user = get_user(self.request)
        context['site_title'] = '%s | %s' % (self.problem.title, get_option('site_title'))
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['title'] = self.problem.title
        context['sidebar'] = True
        context['problem'] = self.problem
        context['problem_perm_manage'] = permissions.problem(obj=self.problem, user=user, mode='manage')
        context['problem_perm_contribute'] = permissions.problem(obj=self.problem, user=user, mode='contribute')
        context['comments'] = models.Comment.objects.filter(problem=self.problem)
        context['comment_form'] = forms.CommentForm()
        context['contributor_form'] = forms.ContributorForm(problem=self.problem.id)
        context['all_ideas'] = models.Idea.objects.filter(problem=self.problem)

        # Criterias

        context['criterias'] = list()
        for c in models.Criteria.objects.filter(problem=self.problem):
            c.problem_count = models.Problem.objects.filter(criteria=c).count()
            context['criterias'].append(c)

        # Alternatives

        context['alternatives'] = list()
        for a in models.Alternative.objects.filter(problem=self.problem):
            a.fill_data(self.request.user)
            context['alternatives'].append(a)

        # Ideas

        ideas_qs = Q(problem=self.problem) & permissions.idea_queryset(user=user)
        if ideas_qs:
            context['ideas'] = models.Idea.objects.filter(ideas_qs)
        else:
            context['ideas'] = models.Idea.objects.none()
        context['idea_actions'] = True

        # Voting and comments

        for idea in context['ideas']:
            idea.fill_data(user=self.request.user)

        for comment in context['comments']:
            comment.perm_manage = permissions.comment(obj=comment, user=self.request.user, mode='manage')

        return context

    def get_breadcrumbs(self):
        return [
            { 'title': self.problem.title, 'url': self.problem.get_absolute_url(), 'classes': 'current' } ]

    def form_valid(self, form):
        return idea_save(self, form)

class ProblemActivityView(TemplateView):
    template_name = 'activity.html'

    def dispatch(self, request, *args, **kwargs):
        self.problem = get_object_or_404(models.Problem, slug=self.kwargs['slug'])
        if not permissions.problem(obj=self.problem, user=self.request.user, mode='contribute'):
            raise PermissionDenied
        return super(ProblemActivityView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(ProblemActivityView, self).get_context_data(**kwargs)
        activities = Paginator(any_stream(self.problem), 20)
        context['site_title'] = '%s | %s' % (self.problem.title, _('Problem activity'))
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['problem'] = self.problem
        context['activities'] = activities.page(self.request.GET.get('page', 1))
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': self.problem.title, 'url': self.problem.get_absolute_url() },
            { 'title': _('Activity'), 'url': reverse('problem_activity', kwargs={'slug':self.problem.slug}), 'classes': 'current' } ]
