from datetime import datetime
from lxml.html.diff import htmldiff
import bleach
import re
import time
import string
import random

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
from django.utils.safestring import mark_safe
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

class ProblemCreateView(RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        """
        Creates a draft problem for the user to start edition.
        """
        if self.request.user.is_authenticated():
            p = models.Problem.objects.create(
                published=False,
                slug=''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(100)),
                author=self.request.user)
            return reverse('problem_update', kwargs={'pk': p.id})
        return Http404()

class ProblemUpdateView(UpdateView):
    template_name = 'problem_update.html'
    form_class = forms.ProblemForm
    model = models.Problem

    @method_decorator(login_required)
    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        obj = get_object_or_404(models.Problem, id=kwargs['pk'])
        if not permissions.problem(obj=obj, user=self.request.user, mode='edit'):
            raise PermissionDenied
        self.problem = obj
        return super(ProblemUpdateView, self).dispatch(*args, **kwargs)

    def post(self, *args, **kwargs):
        """
        Checks for a delete action from forms.DeleteForm.
        """

        yes = args[0].POST.get('yes', None)
        try:
            delete_problem = int(args[0].POST.get('delete_problem', ''))
        except ValueError:
            delete_problem = False
        if delete_problem:
            if yes and delete_problem == self.problem.id and \
                permissions.problem(obj=self.problem, user=args[0].user, mode='manage'):
                self.problem.delete()
                messages.success(args[0], _('The problem was deleted.'))
                return HttpResponseRedirect(reverse('home'))
            elif not yes:
                messages.warning(args[0], _('You need to mark the confirmation checkbox if you want to delete the form.'))

        return super(ProblemUpdateView, self).post(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(ProblemUpdateView, self).get_context_data(**kwargs)
        context['site_title'] = '%s | %s' % (self.object.title, _('Edit'))
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['delete_form'] = forms.DeleteForm()
        context['criteria_form'] = forms.CriteriaForm()
        context['title'] = _('Edit problem')
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Update'), 'url': reverse('problem_update', kwargs={'pk':self.object.id}), 'classes': 'current' } ]

    def get_form_kwargs(self):
        kwargs = super(ProblemUpdateView, self).get_form_kwargs()
        kwargs['problem_perm_edit'] = permissions.problem(obj=self.problem, user=self.request.user, mode='edit')
        kwargs['problem_perm_manage'] = permissions.problem(obj=self.problem, user=self.request.user, mode='manage')
        return kwargs

    def form_valid(self, form):
        """
        Save the object, clear the criteria and add the submitted ones in
        ``request.POST``.
        """

        self.object = form.save(commit=False)

        # Remember if new

        old = get_object_or_404(models.Problem, id=self.object.id)
        old_diffhtml = render_to_string('problem_diffbase.html', {'problem': old})

        # Problem save

        self.object.author = self.request.user if not self.object.author else self.object.author
        self.object.description = bleach.clean(self.object.description,
            tags=settings.SANITIZER_ALLOWED_TAGS,
            attributes=settings.SANITIZER_ALLOWED_ATTRIBUTES,
            styles=settings.SANITIZER_ALLOWED_STYLES,
            strip=True, strip_comments=True)
        self.object.published = True if self.request.POST.get('publish', None) else False
        self.object.save()

        if self.object.author.id != self.request.user.id and self.object.open:
            self.object.coauthor.add(obj.request.user)
        elif self.object.author.id != self.request.user.id and not self.object.open:
            raise HttpResponseForbidden

        self.object.save()

        # Get a content diff

        new_diffhtml = render_to_string('problem_diffbase.html', {'problem': self.object})
        problemdiff = htmldiff(old_diffhtml, new_diffhtml)

        # Follow and send an action for the problem

        follow(self.request.user, self.object, actor_only=False) if not is_following(self.request.user, self.object) else None
        if self.object.published:
            a = action.send(self.request.user, verb='edited', action_object=self.object)
            if problemdiff:
                a[0][1].data = {'diff': problemdiff}
                a[0][1].save()
            activity_count(self.object)

        if not self.object.published:
            view = 'problem_update'
            kwargs = { 'pk': self.object.id }
            messages.success(self.request, mark_safe(_('The problem was successfully saved as a draft. <a class="left-1em button success tiny radius" target="_blank" href="%s">Preview</a>' % reverse('problem', kwargs={'pk': self.object.id, 'slug': self.object.slug}))))
        else:
            view = 'problem'
            kwargs = { 'pk': self.object.id, 'slug': self.object.slug }
            messages.success(self.request, _('The problem is now published. Users can start contributing to it.'))
        return HttpResponseRedirect(reverse(view, kwargs=kwargs))

class ProblemView(TemplateView):
    template_name = 'problem.html'

    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        """
        Redirects to the full ``problems/<id>/<slug>`` URL format of a problem,
        and make the usual permission check if it's the valid URL.
        """
        self.object = get_object_or_404(models.Problem, id=kwargs['pk'])
        if 'slug' not in kwargs or kwargs['slug'] != self.object.slug:
            return HttpResponseRedirect(reverse('problem', kwargs={'pk': self.object.id, 'slug': self.object.slug}))
        if not permissions.problem(obj=self.object, user=self.request.user, mode='view'):
            raise PermissionDenied
        return super(ProblemView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(ProblemView, self).get_form_kwargs()
        kwargs['problem'] = self.object
        return kwargs

    def get_context_data(self, *args, **kwargs):
        context = super(ProblemView, self).get_context_data(**kwargs)
        user = get_user(self.request)
        coauthor = self.object.coauthor.count()
        context['site_title'] = '%s | %s' % (self.object.title, get_option('site_title'))
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['title'] = self.object.title
        context['sidebar'] = True
        context['problem'] = self.object
        context['problem_perm_manage'] = permissions.problem(obj=self.object, user=user, mode='manage')
        context['problem_perm_edit'] = permissions.problem(obj=self.object, user=user, mode='edit')
        context['problem_perm_contribute'] = permissions.problem(obj=self.object, user=user, mode='contribute')
        context['comments'] = models.Comment.objects.filter(problem=self.object)
        context['comment_form'] = forms.CommentForm()
        context['comment_form_problem'] = forms.CommentForm(initial={'problem': self.object.id})
        context['contributor_form'] = forms.ContributorForm(problem=self.object.id)
        context['ideas'] = models.Idea.objects.filter(problem=self.object.id, published=True)
        for i in context['ideas']: i.fill_data(self.request.user);
        context['delete_form'] = forms.DeleteForm()

        # Criterias

        context['criteria'] = list()
        for c in models.Criteria.objects.filter(problem=self.object):
            c.problem_count = models.Problem.objects.filter(criteria=c).count()
            c.fill_data()
            context['criteria'].append(c)

        # Alternatives

        context['alternatives'] = list()
        for a in models.Alternative.objects.filter(problem=self.object):
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
            { 'title': self.object.title, 'url': self.object.get_absolute_url(), 'classes': 'current' } ]

class ProblemActivityView(TemplateView):
    template_name = 'activity.html'

    def dispatch(self, request, *args, **kwargs):
        self.problem = get_object_or_404(models.Problem, slug=self.kwargs.get('pk', None))
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
