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
from django.views.generic.edit import FormView, CreateView, UpdateView

from actstream.models import any_stream

from dnstorm import settings
from dnstorm.app import forms
from dnstorm.app import models
from dnstorm.app import permissions
from dnstorm.app.utils import get_object_or_none, activity_count, get_option, activity_register

def problem_buttons(request, obj):
    url_name = request.resolver_match.url_name
    user = get_user(request)
    return [
        {
            'icon': 'page-export',
            'title': _('Published') if obj.published else _('Draft'),
            'url': reverse('problem', kwargs={'pk': obj.id, 'slug':obj.slug}),
            'marked': url_name == 'problem',
            'show': True
        },{
            'icon': 'pencil',
            'title': _('Edit'),
            'url': reverse('problem_update', kwargs={'pk': obj.id}),
            'marked': url_name == 'problem_update',
            'show': permissions.problem(obj=obj, user=request.user, mode='edit')
        },{
            'icon': 'list',
            'title': _('Activity'),
            'url': reverse('activity_problem', kwargs={'pk': obj.id }),
            'marked': url_name in ['activity_problem', 'activity_problem_objects', 'activity_problem_object'],
            'show': True,
        },{
            'icon': 'torso',
            'title': _('Contributors and permissions') if permissions.problem(obj=obj, user=request.user, mode='manage') else _('Contributors'),
            'url': reverse('problem_contributors', kwargs={'pk': obj.id}),
            'marked': url_name == 'problem_contributors',
            'show': True
        }
    ]

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
    template_name = '_update_problem.html'
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
        context['info'] = self.get_info()
        context['delete_form'] = forms.DeleteForm()
        context['title'] = _('Edit problem')
        return context

    def get_form_kwargs(self):
        kwargs = super(ProblemUpdateView, self).get_form_kwargs()
        kwargs['problem_perm_edit'] = permissions.problem(obj=self.problem, user=self.request.user, mode='edit')
        kwargs['problem_perm_manage'] = permissions.problem(obj=self.problem, user=self.request.user, mode='manage')
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """
        Save the object, clear the criteria and add the submitted ones in
        ``request.POST``.
        """

        self.object = form.save(commit=False)

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
            raise PermissionDenied

        self.object.save()

        # Response
        if not self.object.published:
            view = 'problem_update'
            kwargs = { 'pk': self.object.id }
            messages.success(self.request, mark_safe(_('The problem was successfully saved as a draft. <a class="left-1em button success tiny radius" target="_blank" href="%s">Preview</a>' % reverse('problem', kwargs={'pk': self.object.id, 'slug': self.object.slug}))))
        else:
            view = 'problem'
            kwargs = { 'pk': self.object.id, 'slug': self.object.slug }
            messages.success(self.request, _('The problem was successfuly saved.'))
            activity_register(self.request.user, self.object)
        return HttpResponseRedirect(reverse(view, kwargs=kwargs))

    def get_info(self):
        return {
            'icon': 'pencil',
            'icon_url': reverse('problem', kwargs={'pk': self.object.id, 'slug': self.object.slug}),
            'title': _('Edit problem: %s' % self.object.title),
            'title_url': self.object.get_absolute_url(),
            'buttons': problem_buttons(self.request, self.object),
            'show': permissions.problem(obj=self.object, user=self.request.user, mode='edit')
        }

class ProblemContributorView(FormView):
    template_name = '_update_problem_contributors.html'
    form_class = forms.ProblemContributorForm

    def dispatch(self, request, *args, **kwargs):
        # Permissions
        self.object = get_object_or_404(models.Problem, id=kwargs['pk'])
        if not permissions.problem(obj=self.object, user=request.user, mode='view'):
            raise PermissionDenied
        # OK
        return super(ProblemContributorView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(ProblemContributorView, self).get_form_kwargs()
        kwargs['problem'] = self.object
        return kwargs

    def get_context_data(self, *args, **kwargs):
        context = super(ProblemContributorView, self).get_context_data(**kwargs)
        context['site_title'] = '%s | %s' % (self.object.title, _('Contributors'))
        context['info'] = self.get_info()
        context['title'] = _('Problem contributors')
        context['delete_form'] = forms.DeleteForm()
        context['problem'] = self.object
        context['users'] = self.object.contributor.all()
        context['problem_perm_manage'] = permissions.problem(obj=self.object, user=self.request.user, mode='manage')
        return context

    def form_valid(self, form):
        """
        Save the contributors and problem status.
        """
        # permissions
        if not permissions.problem(obj=self.object, user=self.request.user, mode='manage'):
            raise PermissionDenied
        # commit
        form.problem.open = form.cleaned_data.get('open', False)
        form.problem.public = form.cleaned_data.get('public', False)
        form.problem.save()
        messages.success(self.request, mark_safe(_('Permission options in the problem was successfully saved.')))
        return HttpResponseRedirect(reverse('problem', kwargs={'pk': form.problem.id, 'slug': form.problem.slug}))

    def get_info(self):
        return {
            'icon': 'torso',
            'icon_url': reverse('problem_contributors', kwargs={'pk': self.object.id }),
            'title': _('Problem contributors: %s' % self.object.title),
            'title_url': self.object.get_absolute_url(),
            'buttons': problem_buttons(self.request, self.object),
            'show': permissions.problem(obj=self.object, user=self.request.user, mode='view'),
        }

class ProblemView(TemplateView):
    template_name = '_single_problem.html'

    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        """
        Redirects to the full ``problems/<id>/<slug>`` URL format of a problem,
        and make the usual permission check if it's the valid URL.
        """
        self.object = get_object_or_404(models.Problem, id=kwargs['pk'])
        if 'slug' not in kwargs or kwargs['slug'] != self.object.slug:
            return HttpResponseRedirect(reverse('problem', kwargs={'pk': self.object.id, 'slug': self.object.slug}))
        if not permissions.problem(obj=self.object, user=request.user, mode='view'):
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
        context['info'] = self.get_info()
        context['tabs'] = self.get_tabs()
        context['title'] = self.object.title
        context['sidebar'] = True
        context['problem'] = self.object
        context['problem_perm_manage'] = permissions.problem(obj=self.object, user=user, mode='manage')
        context['problem_perm_edit'] = permissions.problem(obj=self.object, user=user, mode='edit')
        context['problem_perm_contribute'] = permissions.problem(obj=self.object, user=user, mode='contribute')
        context['comments'] = models.Comment.objects.filter(problem=self.object)
        context['comment_form'] = forms.CommentForm()
        context['delete_form'] = forms.DeleteForm()
        context['alternative_form'] = forms.AlternativeForm()

        # Contributors
        if self.request.resolver_match.url_name == 'problem_contributors':
            context['contributors'] = self.object.contributor.filter(is_staff=True).order_by('first_name')
            return context

        # Criterias
        context['criteria'] = list()
        for c in models.Criteria.objects.filter(problem=self.object):
            c.problem_count = models.Problem.objects.filter(criteria=c).count()
            c.fill_data(user)
            context['criteria'].append(c)
        context['criteria'] = sorted(context['criteria'], key=lambda x: (x.weight))

        # Ideas
        context['ideas'] = models.Idea.objects.filter(problem=self.object.id, published=True)
        for idea in context['ideas']:
            idea.fill_data(user)
        context['ideas'] = sorted(context['ideas'], key=lambda x: (x.votes, x.updated, x.created), reverse=True)

        # Alternatives
        context['alternatives'] = list()
        for a in models.Alternative.objects.filter(problem=self.object):
            a.fill_data(user)
            context['alternatives'].append(a)
        context['alternatives'] = sorted(context['alternatives'], key=lambda x: (x.vote_value, x.updated, x.created), reverse=True)

        # Comments
        for comment in context['comments']:
            comment.perm_manage = permissions.comment(obj=comment, user=self.request.user, mode='manage')

        # Results
        self.object.fill_data(user)

        return context

    def get_info(self):
        return {
            'icon': 'target-two',
            'icon_url': reverse('problem', kwargs={'pk': self.object.id, 'slug': self.object.slug}),
            'title': self.object.title,
            'title_url': self.object.get_absolute_url(),
            'buttons': problem_buttons(self.request, self.object),
            'show': True
        }

    def get_tabs(self):
        return {
            'classes': 'problem-tabs',
            'items': [{
                'icon': 'target-two', 'name': _('Problem'),
                'classes': 'problem-tab-selector small-12 medium-2 medium-offset-1',
                'data': 'description',
                'show': True
            },{
                'icon': 'cloud', 'name': _('Criteria'),
                'classes': 'problem-tab-selector small-12 medium-2',
                'data': 'criteria',
                'show': True
            },{
                'icon': 'lightbulb', 'name': _('Ideas'),
                'classes': 'problem-tab-selector small-12 medium-2',
                'data': 'ideas',
                'show': True
            },{
                'icon': 'list', 'name': _('Alternatives'),
                'classes': 'problem-tab-selector small-12 medium-2',
                'data': 'alternatives',
                'show': True
            },{
                'icon': 'play', 'name': _('Results'),
                'classes': 'problem-tab-selector small-12 medium-2 medium-pull-1',
                'data': 'results',
                'show': True
            }]
        }
