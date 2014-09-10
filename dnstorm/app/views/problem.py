import re
import time
from datetime import datetime

from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseRedirect
from django.views.generic import DetailView
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView
from django.views.generic.base import TemplateView, RedirectView
from django.contrib.auth import get_user
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.db.models import Q
from django.db.models.query import EmptyQuerySet
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

import bleach
import diff_match_patch as _dmp
from actstream import action
from actstream.actions import follow, unfollow
from actstream.models import followers
from notification import models as notification

from dnstorm import settings
from dnstorm.app import permissions
from dnstorm.app.lib.diff import diff_prettyHtml
from dnstorm.app.lib.get import get_object_or_none
from dnstorm.app import models
from dnstorm.app import forms
from dnstorm.app.views.idea import idea_save

def problem_save(obj, form):
    """
    Save the object, clear the criterias and add the submited ones in
    ``request.POST``. This method will be the same for ProblemCreateView and
    ProblemUpdateView.
    """

    # Remember if new

    new = False if hasattr(obj.object, 'id') and isinstance(obj.object.id, int) else True

    # Save first

    obj.object = form.save(commit=False)
    obj.object.author = obj.request.user
    obj.object.description = bleach.clean(obj.object.description,
        tags=settings.SANITIZER_ALLOWED_TAGS,
        attributes=settings.SANITIZER_ALLOWED_ATTRIBUTES,
        styles=settings.SANITIZER_ALLOWED_STYLES,
        strip=True, strip_comments=True)
    obj.object.save()

    # Criterias

    obj.object.criteria.clear()
    criterias = [i for i in obj.request.POST.get('criteria', '').split('|') if i.isdigit()]
    for c in models.Criteria.objects.filter(id__in=criterias):
        obj.object.criteria.add(c)

    # Invitations

    from_user = obj.object.author.get_full_name()
    emails = [u.email for u in obj.object.contributor.all()]
    to_add = list()

    for email in sorted(set(obj.request.POST.getlist('invitation', []))):

        # User already invited
        if models.Invitation.objects.filter(problem=obj.object.id, email=email).exists():
            continue

        # User is already a contributor
        if email in emails:
            continue

        # Save user to add as contributor if exists
        user = get_object_or_none(User, email=email)
        if user:
            to_add.append(user)
            continue

        models.Invitation(problem=obj.object, email=email).save()
        fake_user = User(id=1, username=i, email=email)
        notification.send([fake_user], 'invitation', { 'from_user': from_user, 'problem': obj.object })

    # Update contributors

    new_contributors = User.objects.filter(id__in=[i for i in obj.request.POST.get('contributor', '').split('|') if i.isdigit()])
    if not new_contributors:
        obj.object.contributor.through.objects.all().delete()
    current_contributors = obj.object.contributor.all()

    c = [c.id for c in list(set(current_contributors) - set(new_contributors))]
    obj.object.contributor.through.objects.filter(id__in=c).delete()

    c = list(set(new_contributors) - set(current_contributors))
    for u in c:
        obj.object.contributor.add(u)
        notification.send([u], 'contributor', { 'from_user': from_user, 'problem': obj.object })

    for user in to_add:
        obj.object.contributor.add(user)
        follow(user, obj.object)

    obj.object.save()

    # Success

    _c = [o for o in obj.object.contributor.all()] + [obj.object.author]
    _f = followers(obj.object)
    for f in _f:
        unfollow(f, obj.object) if f not in _c else None
    for c in _c:
        follow(c, obj.object, actor_only=False) if c not in _f else None

    # Send an action

    verb = 'created' if new else 'edited'
    action.send(obj.object.author, verb=verb, action_object=obj.object)

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
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['title'] = _('Create new problem')
        context['criteria_form'] = forms.CriteriaForm()
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Problems'), 'url': reverse('home') },
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
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['title'] = _('Edit problem')
        context['criteria_form'] = forms.CriteriaForm()
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Problems'), 'url': reverse('home') },
            { 'title': self.object.title, 'url': self.object.get_absolute_url() },
            { 'title': _('Update'), 'url': reverse('problem_edit', kwargs={'slug':self.object.slug}), 'classes': 'current' } ]

    def form_valid(self, form):
        return problem_save(self, form)

class ProblemDeleteView(DeleteView):
    template_name = 'problem_confirm_delete.html'
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
        if not permissions.problem(obj=self.problem, user=self.request.user, mode='contribute'):
            raise PermissionDenied
        return super(ProblemView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(ProblemView, self).get_form_kwargs()
        kwargs['problem'] = self.problem
        return kwargs

    def get_context_data(self, *args, **kwargs):
        context = super(ProblemView, self).get_context_data(**kwargs)
        user = get_user(self.request)
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['title'] = self.problem.title
        context['sidebar'] = True
        context['problem'] = self.problem
        context['problem_perm_manage'] = permissions.problem(obj=self.problem, user=user, mode='manage')
        context['problem_perm_contribute'] = permissions.problem(obj=self.problem, user=user, mode='contribute')
        context['comments'] = models.Comment.objects.filter(problem=self.problem)
        context['comment_form'] = forms.CommentForm()
        context['criterias'] = models.Criteria.objects.filter(problem=self.problem)
        context['all_ideas'] = models.Idea.objects.filter(problem=self.problem)

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
            { 'title': _('Problems'), 'url': reverse('home') },
            { 'title': self.problem.title, 'url': self.problem.get_absolute_url(), 'classes': 'current' } ]

    def form_valid(self, form):
        return idea_save(self, form)
