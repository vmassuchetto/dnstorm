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
    if not new:
        old = get_object_or_404(models.Problem, id=obj.object.id)
        old_diffhtml = render_to_string('problem_diffbase.html', {'problem': old}) if not new else None

    # Save problem

    obj.object.author = obj.request.user if new else old.author
    obj.object.description = bleach.clean(obj.object.description,
        tags=settings.SANITIZER_ALLOWED_TAGS,
        attributes=settings.SANITIZER_ALLOWED_ATTRIBUTES,
        styles=settings.SANITIZER_ALLOWED_STYLES,
        strip=True, strip_comments=True)
    obj.object.save()

    if permissions.problem(obj=obj.object, user=obj.request.user, mode='manage'):
        obj.object.criteria.clear()
        criterias = [i for i in obj.request.POST.get('criteria', '').split('|') if i.isdigit()]
        for c in models.Criteria.objects.filter(id__in=criterias):
            obj.object.criteria.add(c)

    if obj.object.author.id != obj.request.user.id:
        obj.object.coauthor.add(obj.request.user)

    obj.object.save()

    # Get a content diff

    new_diffhtml = render_to_string('problem_diffbase.html', {'problem': obj.object})
    if not new:
        problemdiff = htmldiff(old_diffhtml, new_diffhtml)
    else:
        problemdiff = new_diffhtml

    # Follow and send an action for the problem

    follow(obj.request.user, obj.object, actor_only=False) if not is_following(obj.request.user, obj.object) else None
    a = action.send(obj.request.user, verb='created' if new else 'edited', action_object=obj.object)
    if problemdiff:
        a[0][1].data = {'diff': problemdiff}
        a[0][1].save()
    activity_count(obj.object)

    messages.success(obj.request, _('Problem saved'))
    return HttpResponseRedirect(reverse('problem', kwargs={'slug':obj.object.slug}))

class ProblemCreateView(CreateView):
    template_name = 'problem_update.html'
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
            { 'title': _('Create new problem'), 'url': reverse('problem_create'), 'classes': 'current' } ]

    def form_valid(self, form):
        return problem_save(self, form)

class ProblemUpdateView(UpdateView):
    template_name = 'problem_update.html'
    form_class = forms.ProblemForm
    model = models.Problem

    @method_decorator(login_required)
    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        obj = get_object_or_404(models.Problem, slug=kwargs['slug'])
        if not permissions.problem(obj=obj, user=self.request.user, mode='edit'):
            raise PermissionDenied
        self.problem = obj
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
            { 'title': _('Update'), 'url': reverse('problem_update', kwargs={'slug':self.object.slug}), 'classes': 'current' } ]

    def form_valid(self, form):
        return problem_save(self, form)

    def get_form_kwargs(self):
        kwargs = super(ProblemUpdateView, self).get_form_kwargs()
        if self.request.POST.get('title', None) \
            and self.request.POST.get('description', None) \
            and 'criteria' not in self.request.POST \
            and permissions.problem(obj=self.problem, user=self.request.user, mode='edit'):
            kwargs['criteria_required'] = False
        else:
            kwargs['criteria_required'] = True
        kwargs['problem_perm_edit'] = permissions.problem(obj=self.problem, user=self.request.user, mode='edit')
        kwargs['problem_perm_manage'] = permissions.problem(obj=self.problem, user=self.request.user, mode='manage')
        return kwargs

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

    def post(self, *args, **kwargs):
        """
        Checks for delete actions of problem, ideas and comments sent from
        forms.DeleteForm.
        """

        yes = args[0].POST.get('yes', None)

        # Delete problem

        try:
            delete_problem = int(args[0].POST.get('delete_problem', None))
        except ValueError:
            delete_problem = False
        if delete_problem:
            if yes and delete_problem == self.problem.id and \
                permissions.problem(obj=self.problem, user=args[0].user, mode='manage'):
                self.problem.delete()
                messages.success(args[0], _('The problem was deleted.'))
                return HttpResponseRedirect(reverse('home'))

        # Delete idea

        try:
            delete_idea = int(args[0].POST.get('delete_idea', None))
        except ValueError:
            delete_idea = False
        if delete_idea:
            idea = get_object_or_404(models.Idea, id=delete_idea)
            if yes and permissions.idea(obj=idea, user=args[0].user, mode='manage'):
                idea.delete()
                messages.success(args[0], _('The idea was deleted.'))
                return HttpResponseRedirect(reverse('problem', kwargs={'slug':self.problem.slug}))


        if not yes and (delete_problem or delete_idea):
            messages.warning(args[0], _('You need to mark the checkbox to really delete.'))
            return HttpResponseRedirect(reverse('problem', kwargs={'slug':self.problem.slug}))

        # Delete comment

        try:
            delete_comment = int(args[0].POST.get('delete_comment', None))
        except ValueError:
            delete_comment = False
        if delete_comment:
            comment = get_object_or_404(models.Comment, id=delete_comment)
            if yes and permissions.comment(obj=comment, user=args[0].user, mode='manage'):
                comment.delete()
                messages.success(args[0], _('The comment was deleted.'))
                return HttpResponseRedirect(reverse('problem', kwargs={'slug':self.problem.slug}))

        if not yes and (delete_problem or delete_idea or delete_comment):
            messages.warning(args[0], _('You need to mark the checkbox to really delete.'))
            return HttpResponseRedirect(reverse('problem', kwargs={'slug':self.problem.slug}))

        return super(ProblemView, self).post(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(ProblemView, self).get_context_data(**kwargs)
        user = get_user(self.request)
        coauthor = self.problem.coauthor.count()
        context['site_title'] = '%s | %s' % (self.problem.title, get_option('site_title'))
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['title'] = self.problem.title
        context['sidebar'] = True
        context['problem'] = self.problem
        context['problem_perm_manage'] = permissions.problem(obj=self.problem, user=user, mode='manage')
        context['problem_perm_edit'] = permissions.problem(obj=self.problem, user=user, mode='edit')
        context['problem_perm_contribute'] = permissions.problem(obj=self.problem, user=user, mode='contribute')
        context['coauthor'] = self.problem.coauthor.all()[coauthor-1] if coauthor > 0 else None
        context['comments'] = models.Comment.objects.filter(problem=self.problem)
        context['comment_form'] = forms.CommentForm()
        context['contributor_form'] = forms.ContributorForm(problem=self.problem.id)
        context['ideas'] = models.Idea.objects.filter(problem=self.problem)
        context['delete_form'] = forms.DeleteForm(problem=self.problem.id)

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

        # Voting and comments

        for idea in context['ideas']:
            idea.fill_data(user=self.request.user)
        context['ideas'] = sorted(context['ideas'], key=lambda x: (x.votes, x.updated, x.created), reverse=True)

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
