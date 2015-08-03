import bleach
import json
import random
import re
import string
import time
import urlparse

from datetime import datetime
from lxml.html.diff import htmldiff

from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, login, get_user
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import login as login_view
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse, resolve
from django.db.models import Q, Sum
from django.db.models.query import EmptyQuerySet
from django.forms.util import ErrorList
from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseForbidden, HttpResponseServerError, QueryDict
from django.shortcuts import get_object_or_404, render
from django.template import loader, Context
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_protect
from django.views.generic import DetailView, RedirectView
from django.views.generic import View
from django.views.generic.base import TemplateView, RedirectView, View, TemplateResponseMixin
from django.views.generic.detail import SingleObjectTemplateResponseMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView, UpdateView

from actstream import action
from actstream.actions import follow, unfollow, is_following
from actstream.models import Action, actor_stream, any_stream
from crispy_forms.utils import render_crispy_form
from notification import models as notification
from registration import signals as registration_signals
from registration.backends.default.views import RegistrationView as BaseRegistrationView

from dnstorm import settings
from dnstorm.app import models, forms, perms, utils
from dnstorm.app.templatetags.user_tags import user_problem_count, user_idea_count, user_comment_count

#
# Mixins {{{
#

class DeleteMixin(object):
    """
    Common delete operation.
    """
    template_name = 'confirm_delete.html'

    def get_object(self, *args, **kwargs):
        """
        Finds the object to be deleted.
        """
        obj = get_object_or_404(self.model, id=self.kwargs['pk'])
        if not getattr(perms, obj.__class__.__name__.lower())(self.request.user, 'delete', obj):
            raise PermissionDenied
        return obj

    def get_success_url(self):
        messages.success(self.request, _('The %s was deleted successfully' % self.object._meta.verbose_name))
        obj = self.object.problem if hasattr(self.object, 'problem') else self.object
        return reverse('problem_tab_%s' % self.object.__class__.__name__.lower(), kwargs={'pk': obj.id, 'slug': obj.slug})

#
# }}} Authentication {{{
#

class LoginRequiredMixin(TemplateResponseMixin):

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            raise PermissionDenied()
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)

class SuperUserRequiredMixin(TemplateResponseMixin):

    def dispatch(self, *args, **kwargs):
        self.request.user = get_user(self.request)
        if not self.request.user.is_superuser:
            raise PermissionDenied()
        return super(SuperUserRequiredMixin, self).dispatch(*args, **kwargs)

class RegistrationView(BaseRegistrationView):
    form_class = forms.RegistrationForm

    def get_form_kwargs(self, request=None):
        kwargs = super(RegistrationView, self).get_form_kwargs(request)
        kwargs['hash'] = self.request.GET.get('hash', self.request.POST.get('hash', None))
        return kwargs

    def get_info(self):
        """
        Information for the title bar.
        """
        return {
            'icon': 'torso',
            'icon_url': reverse('registration_register'),
            'title': _('Registration'),
            'show': True
        }

    def register(self, request, **cleaned_data):
        """
        Defaul User model flags are used in combination to define the following statuses:

        * superuser = is_superuser=True
        * active: is_active=True and is_staff=True
        * invitation: is_active=True and is_staff=False
        * inactive: is_active=False and is_staff=False

        Register the user checking for invitations. Django default user fields
        are filled as follow:

        * username
          - active user: displayed username
          - invitation: e-mail
          - inactive user: u<user_id>
        * first_name
          - active user: displayed real name set by user
          - invitation: e-mail
          - inactive user: u<user_id>
        * last_name
          - always a backup of first_name
        """
        # Invited user
        _hash = cleaned_data.get('hash', None)
        if len(_hash) > 2:
            invitation = get_object_or_404(models.Invitation, hash=_hash)
            user = invitation.user
            user.username, user.email, user.first_name, \
                user.last_name, user.is_active, user.is_staff = \
                cleaned_data['username'], cleaned_data['email'], \
                cleaned_data['username'], cleaned_data['username'], \
                True, True
            user.set_password(cleaned_data['password1'])
            user.save()
        # New registration
        else:
            user = User.objects.create(
                username=cleaned_data['username'], email=cleaned_data['email'],
                first_name=cleaned_data['username'], last_name=cleaned_data['username'],
                is_active=True, is_staff=True, date_joined=datetime.now())
            user.set_password(cleaned_data['password1'])
            user.save()
            # Log in
            _user = authenticate(username=cleaned_data['username'], password=cleaned_data['password1'])
            login(self.request, _user)
            messages.success(self.request, _('Welcome to DNStorm. A confirmation e-mail was sent to you.'))
            return _user

        # delete invitations
        for i in models.Invitation.objects.filter(user=user):
            i.delete()

        # Log in
        _user = authenticate(username=cleaned_data['username'], password=cleaned_data['password1'])
        login(self.request, _user)

        # Response
        messages.success(self.request, _('Welcome to DNStorm. A confirmation e-mail was sent to you.'))
        return HttpResponseRedirect(reverse('home'))

class LoginView(View):
    """
    Redirects valid users to the 'home' or 'next' page instead of showing the
    login form.
    """

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated():
            next = self.request.GET.get('next', None)
            next = next if next else reverse('home')
            return HttpResponseRedirect(next)
        else:
            return login_view(self.request)

    def post(self, *args, **kwargs):
        return self.get(*args, **kwargs)

#
# }}} Ajax {{{
#

class AjaxView(View):
    """
    Ajax actions view. Will receive all GET and POST requests to /ajax/ URL.
    """

    def get(self, *args, **kwargs):
        """
        Ajax GET requests router.
        """
        # Validation
        if not self.request.is_ajax():
            raise Http404

        # Delete
        # collaborator
        elif self.request.GET.get('collaborator_delete', None):
            return self.collaborator_delete()

        # Create
        # collaborator
        elif self.request.GET.get('collaborator_add', None):
            return self.collaborator_add()
        # idea
        elif self.request.GET.get('idea_like', None):
            return self.idea_like()
        # alternative
        elif self.request.GET.get('alternative_like', None):
            return self.alternative_like()
        # activity
        elif self.request.GET.get('activity_reset_counter', None):
            return self.activity_reset_counter()

        # Get
        # users
        elif self.request.GET.get('user_search', None):
            return self.user_search()
        # help
        elif self.request.GET.get('help', None):
            return self.get_help()

        # Failure
        return HttpResponseForbidden()

    def post(self, *args, **kwargs):
        """
        Ajax POST requests router.
        """
        # Validation
        if not self.request.is_ajax():
            raise Http404

        # Comment
        elif self.request.POST.get('comment_new', None):
            return self.comment_new()

        # Failure
        return HttpResponseForbidden()

    def user_search(self):
        """
        Will display an invitation button instead of the user result if what's
        being searched is an e-mail.
        """
        # Validation
        user = get_user(self.request)
        if not user.is_authenticated():
            raise PermissionDenied
        q = self.request.GET.get('user_search', None)
        if not q:
            raise Http404

        # Response
        result = ''
        if utils.is_email(q):
            if User.objects.filter(email=q).exists():
                result = loader.render_to_string('item_user.html', {'user': User.objects.filter(email=q)[0], 'enclosed': True})
            else:
                u = User(username=q, email=q)
                result = loader.render_to_string('item_user.html', {'user': u, 'email_invitation': q, 'enclosed': True})
            return HttpResponse(json.dumps({'result': result}), content_type='application/json')

        for u in User.objects.filter(Q(username__icontains=q) | Q(email__icontains=q))[:10]:
            result += loader.render_to_string('item_user.html', {'user': u, 'enclosed': True})

        return HttpResponse(json.dumps({'result': result}), content_type='application/json')

    def collaborator_add(self):
        """
        Add a user as collaborator for a problem.
        """
        # Validation
        user = utils.get_object_or_none(User, username=self.request.GET['collaborator_add'])
        problem = get_object_or_404(models.Problem, id=self.request.GET['problem'])
        if not perms.problem(self.request.user, 'manage', problem):
            raise PermissionDenied

        # Commit
        # invitation
        if not user and utils.is_email(self.request.GET['collaborator_add']):
            return self.invitation_add()
        # collaborator
        problem.collaborator.add(user)
        follow(user, problem, actor_only=False) if not is_following(user, problem) else None

        # Response
        result = ''.join([loader.render_to_string('item_user_collaborator.html', {'users': problem.collaborator.order_by('first_name')})])
        return HttpResponse(json.dumps({'result': result}), content_type='application/json')

    def collaborator_delete(self):
        """
        Removes a user as collaborator for a problem.
        """
        # Validation
        user = get_object_or_404(User, username=self.request.GET['collaborator_delete'])
        problem = get_object_or_404(models.Problem, id=self.request.GET['problem'])
        if not perms.problem(self.request.user, 'manage', problem):
            raise PermissionDenied

        # Commit
        problem.collaborator.remove(user)
        unfollow(user, problem)
        # delete user and invitations if there's no other invitation
        if not models.Problem.objects.filter(collaborator__in=[user]).exists():
            user.delete()
            models.Invitation.objects.filter(user=user).delete()

        # Response
        result = ''.join([loader.render_to_string('item_user_collaborator.html', {'users': problem.collaborator.order_by('first_name')})])
        return HttpResponse(json.dumps({'result': result}), content_type='application/json')

    def invitation_add(self):
        """
        Invites a user to contribute in a problem. Will let objects created for
        Invitation and User, giving access to the user on RegistrationView.
        """
        # Validation
        problem = get_object_or_404(models.Problem, id=self.request.GET['problem'])
        if not perms.problem(self.request.user, 'manage', problem):
            raise PermissionDenied
        if 'collaborator_add' not in self.request.GET \
            or not utils.is_email(self.request.GET['collaborator_add']):
            raise PermissionDenied

        # Commit
        # user
        email = self.request.GET['collaborator_add']
        user = utils.get_object_or_none(User, email=email)
        password = '%032x' % random.getrandbits(128)
        if not user:
            user = User.objects.create(username=email, email=email, first_name=email,
                password=password,is_active=True, is_staff=False)
        problem.collaborator.add(user)
        # invitation
        hash = '%032x' % random.getrandbits(128)
        while models.Invitation.objects.filter(hash=hash).exists():
            hash = '%032x' % random.getrandbits(128)
        invitation = models.Invitation.objects.create(user=user, hash=hash)
        # notification
        notification.send([user], 'invitation', utils.email_context({ 'invitation': invitation }))

        # Response
        result = ''.join([loader.render_to_string('item_user_collaborator.html', {'users': problem.collaborator.order_by('first_name')})])
        return HttpResponse(json.dumps({'result': result}), content_type='application/json')

    def activity_reset_counter(self):
        """
        Reset the activity counter.
        """
        # Validation
        if not self.request.user.is_authenticated():
            raise Http404

        # Commit
        utils.activity_reset_counter(self.request.user)

        # Response
        return HttpResponse(json.dumps({'ok': 1}), content_type='application/json')

    def criteria_submit(self):
        """
        Submit a criteria for a problem on ProblemUpdateView.
        """
        # Permissions check
        problem = get_object_or_404(models.Problem, id=self.request.POST.get('problem_id'))
        user = get_user(self.request)
        if not perms.problem(user, 'manage', problem):
            raise PermissionDenied

        # Commit
        # set data
        obj = utils.get_object_or_none(models.Criteria, id=self.request.POST.get('id', None))
        self.request.POST = self.request.POST.copy()
        self.request.POST['author'] = user.id
        self.request.POST['description'] = self.request.POST['criteria_description']
        criteria = CriteriaForm(self.request.POST)
        criteria.instance = obj if obj else criteria.instance
        criteria.instance.problem = problem
        # save
        if not criteria.is_valid():
            return HttpResponse(json.dumps({'errors':dict(criteria.errors)}), content_type='application/json')
        criteria.save()
        # reload with updated data
        criteria = CriteriaForm(instance=criteria.instance)
        criteria.instance.get_data()
        # collaborator
        criteria.problem.collaborator.add(user)
        follow(user, criteria.problem, actor_only=False) if not is_following(user, criteria.problem) else None

        # Response
        utils.activity_register(user, criteria.instance)
        result = loader.render_to_string('item_criteria.html', {'criteria': criteria.instance, 'show_actions': True, 'criteria_form': criteria})
        return HttpResponse(json.dumps({'result': result}), content_type='application/json')

    def comment_new(self):
        """
        Comment on a problem, criteria, idea or alternative.
        """
        # Validation
        # user
        user = get_user(self.request)
        # comment
        content = self.request.POST.get('content', None)
        if not content:
            raise Http404
        comment = models.Comment(content=content, author=user)
        # problem
        problem = self.request.POST.get('problem', None)
        if problem:
            _obj = utils.get_object_or_none(models.Problem, id=problem)
            comment.problem = _obj
            _problem = _obj
            target = '#comments-problem-%d' % _obj.id
        # criteria
        criteria = self.request.POST.get('criteria', None)
        if criteria:
            _obj = utils.get_object_or_none(models.Criteria, id=criteria)
            comment.criteria = _obj
            _problem = _obj.problem
            target = '#comments-criteria-%d' % _obj.id
        # idea
        idea = self.request.POST.get('idea', None)
        if idea:
            _obj = utils.get_object_or_none(models.Idea, id=idea)
            comment.idea = _obj
            _problem = _obj.problem
            target = '#comments-idea-%d' % _obj.id
        # alternative
        alternative = self.request.POST.get('alternative', None)
        if alternative:
            _obj = utils.get_object_or_none(models.Alternative, id=alternative)
            comment.alternative = _obj
            _problem = _obj.problem
            target = '#comments-alternative-%d' % _obj.id
        # permissions
        if not problem and not idea and not criteria and not alternative:
            raise Http404
        if not perms.problem(user, 'comment', _problem):
            raise PermissionDenied
        # collaborator
        _problem.collaborator.add(user)
        follow(user, _problem, actor_only=False) if not is_following(user, _problem) else None
        comment.save()

        # Response
        utils.activity_register(user, comment)
        t = loader.get_template('item_comment.html')
        c = Context({'comment': comment})
        return HttpResponse(json.dumps({'target': target, 'html': re.sub("\n", '', t.render(c))}), content_type='application/json')

    def vote_alternative(self):
        """
        Vote for an alternative.
        """
        # Validation
        user = get_user(self.request)
        a = get_object_or_404(models.Alternative, id=self.request.GET.get('vote_alternative'))
        if not a or not user.is_authenticated():
            raise Http404

        # Commit
        vote = models.Vote.objects.filter(alternative=a, author=user)
        if len(vote) > 0:
            vote.delete()
            voted = False
        else:
            models.Vote(alternative=a, author=user).save()
            voted = True

        # Response
        votes = models.Vote.objects.filter(alternative=a).count()
        response = {'votes': votes, 'voted': voted}
        return HttpResponse(json.dumps(response), content_type='application/json')

    def idea_like(self):
        """
        Performs a 'like' and 'unlike' action on an idea.
        """
        # Validation
        user = get_user(self.request)
        idea = get_object_or_404(models.Idea, id=self.request.GET.get('idea_like', None))
        if not perms.idea(user, 'vote', idea):
            return HttpResponseForbidden()

        # Commit
        if models.Vote.objects.filter(idea=idea, author=user).exists():
            models.Vote.objects.filter(idea=idea, author=user).delete()
            voted = False
        else:
            models.Vote.objects.create(idea=idea, author=user)
            voted = True

        # Response
        response = {'counter': idea.vote_count(), 'voted': voted}
        return HttpResponse(json.dumps(response), content_type='application/json')

    def alternative_like(self):
        """
        Applies the 'like' like counter for alternatives.
        """
        # Validation
        user = get_user(self.request)
        alternative = get_object_or_404(models.Alternative, id=self.request.GET.get('alternative_like', None))
        value = self.request.GET.get('value', 0)
        if not perms.problem(user, 'vote', alternative.problem):
            return HttpResponseForbidden()

        # Commit
        obj, created = models.Vote.objects.get_or_create(alternative=alternative, author=user)
        obj.value = value
        obj.save()

        # Response
        response = {'counter': value}
        return HttpResponse(json.dumps(response), content_type='application/json')

    def get_help(self):
        """
        Applies the 'like' like counter for alternatives.
        """
        # Response
        response = {'html': loader.render_to_string('help.html')}
        return HttpResponse(json.dumps(response), content_type='application/json')


# }}} Home page {{{

class HomeView(TemplateView):
    """
    Front landing page.
    """
    template_name = '_home.html'

    def get_context_data(self, *args, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        self.request.user = get_user(self.request)
        authenticated = self.request.user.is_authenticated()

        # problem queryset
        if self.request.resolver_match.url_name == 'home':
            if self.request.user.is_superuser:
                q_problems = Q(published=True)
            elif self.request.user.is_authenticated():
                q_problems = (
                    Q(published=True)
                ) & (
                    (Q(public=True) & Q(open=True)) |
                    Q(collaborator__in=[self.request.user]) |
                    Q(author=self.request.user)
                )
            else:
                q_problems = (Q(published=True) & Q(public=True))
        elif self.request.resolver_match.url_name == 'problems_collaborating':
            q_problems = (Q(published=True) & Q(collaborator__in=[self.request.user]) & ~Q(author=self.request.user))
        elif self.request.resolver_match.url_name == 'problems_drafts':
            q_problems = (Q(published=False) & Q(author=self.request.user))

        if authenticated:
            context['tabs'] = self.get_tabs()
        problems = Paginator(models.Problem.objects.filter(q_problems).distinct().order_by('-last_activity'), 25)
        context['problems'] = problems.page(self.request.GET.get('page', 1))
        context['info'] = self.get_info()
        return context

    def get_info(self):
        return {
            'icon': 'info',
            'title': _('Problems')
        }

    def get_tabs(self):
        return {
            'items': [{
                'classes': 'small-12 medium-2 medium-offset-3',
                'icon': 'web' if not self.request.user.is_superuser else 'asterisk',
                'name': _('Problems') if not self.request.user.is_superuser else _('All'),
                'url': reverse('home'),
                'marked': self.request.resolver_match.url_name == 'home',
                'show': True
            },{
                'classes': 'small-12 medium-2',
                'icon': 'lightbulb', 'name': _('Collaborating'),
                'url': reverse('problems_collaborating'),
                'marked': self.request.resolver_match.url_name == 'problems_collaborating',
                'show': True
            },{
                'classes': 'small-12 medium-2 medium-pull-3',
                'icon': 'page-edit', 'name': _('Drafts'),
                'url': reverse('problems_drafts'),
                'marked': self.request.resolver_match.url_name == 'problems_drafts',
                'show': True
            }]
        }
#
# }}} Options {{{
#

class OptionsView(SuperUserRequiredMixin, FormView):
    """
    Admin options page for superusers.
    """
    template_name = '_update_options.html'
    form_class = forms.OptionsForm

    def get_context_data(self, *args, **kwargs):
        context = super(OptionsView, self).get_context_data(**kwargs)
        context['site_title'] = '%s | %s' % (_('Site options'), utils.get_option('site_title'))
        context['info'] = self.get_info()
        context['title'] = _('Options')
        return context

    def get_info(self):
        return {
            'icon': 'widget',
            'icon_url': reverse('options'),
            'title': _('Options'),
            'show': True
        }

    def form_valid(self, form):

        # Options

        for name in form.cleaned_data:
            utils.update_option(name, form.cleaned_data[name])

        # Update Django site framework

        url = urlparse.urlparse(form.cleaned_data['site_url'])
        utils.update_option('scheme', url.scheme)
        s = Site.objects.get(id=1)
        s.name = form.cleaned_data['site_title']
        s.domain = url.netloc
        s.save()

        messages.success(self.request, mark_safe(_('Options saved.')))
        return HttpResponseRedirect(reverse('options'))
#
# }}} Comments {{{
#

class CommentView(RedirectView):
    """
    Redirects to the '#comment-<id>' URL in a problem.
    """
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        comment = get_object_or_404(models.Comment, id=kwargs['pk'])
        return comment.get_absolute_url()

#
# }}} Users {{{
#

def user_buttons(request, obj):
    return activity_buttons(request) + [{
        'icon': 'pencil',
        'title': _('Edit info'),
        'url': reverse('user_update', kwargs={'username': obj.username}),
        'marked': request.resolver_match.url_name == 'user_update',
        'show': request.user == obj or request.user.is_superuser
    },{
        'icon': 'key',
        'title': _('Change password'),
        'url': reverse('user_password_update', kwargs={'username': obj.username}),
        'marked': request.resolver_match.url_name == 'user_password_update',
        'show': request.user == obj or request.user.is_superuser
    },{
        'icon': 'prohibited',
        'title': _('Inactivate'),
        'url': reverse('user_inactivate', kwargs={'username': obj.username}),
        'show': request.user.is_superuser
    }]

class UserView(LoginRequiredMixin, TemplateView):
    template_name = '_single_activity.html'

    def get_context_data(self, *args, **kwargs):
        context = super(UserView, self).get_context_data(**kwargs)
        self.object = get_object_or_404(User, username=kwargs['username'])
        self.object.problem_count = user_problem_count(self.object)
        self.object.idea_count = user_idea_count(self.object)
        self.object.comment_count = user_comment_count(self.object)
        context['site_title'] = '%s | %s' % (self.object.username, _('User profile'))
        context['profile'] = self.object
        context['info'] = self.get_info()
        activities = Paginator(actor_stream(context['profile']), 25)
        context['activities'] = activities.page(self.request.GET.get('page', 1))
        return context

    def get_info(self):
        return {
            'icon': 'torso',
            'icon_url': reverse('users'),
            'title': _('User activity'),
            'show': True,
            'buttons': user_buttons(self.request, self.object)
        }

class UsersView(LoginRequiredMixin, TemplateView):
    template_name = '_single_users.html'

    def get_context_data(self, *args, **kwargs):
        context = super(UsersView, self).get_context_data(**kwargs)
        self.url_name = self.request.resolver_match.url_name
        self.user_type = self.kwargs.get('user_type', 'active')
        if self.user_type == 'invitations':
            users = User.objects.filter(is_active=True, is_staff=False).order_by('first_name')
        elif self.user_type == 'inactive':
            users = User.objects.filter(is_active=False, is_staff=False).order_by('first_name')
        else:
            users = User.objects.filter(is_active=True, is_staff=True).order_by('first_name')
        page = self.request.GET['page'] if 'page' in self.request.GET else 1
        context['show_user_actions'] = True if self.request.user.is_superuser else False
        context['user_type'] = self.user_type
        context['site_title'] = '%s | %s' % (_('Users'), utils.get_option('site_title'))
        context['info'] = self.get_info()
        context['tabs'] = self.get_tabs()
        context['users'] = Paginator(users, 25).page(page)
        return context

    def get_info(self):
        return {
            'icon': 'torso',
            'icon_url': reverse('home'),
            'title': _('Users'),
            'show': True
        }

    def get_tabs(self):
        return {
            'items': [{
                    'icon': 'torso', 'name': _('Active'),
                    'classes': 'small-12 medium-2 medium-offset-3',
                    'url': reverse('users'),
                    'marked': self.user_type == 'active'
                },{
                    'icon': 'mail', 'name': _('Invitations'),
                    'classes': 'small-12 medium-2',
                    'url': reverse('users_filter', kwargs={'user_type': 'invitations'}),
                    'marked': self.user_type == 'invitations',
                    'show': self.request.user.is_superuser
                },{
                    'icon': 'prohibited', 'name': _('Inactive'),
                    'classes': 'small-12 medium-2 medium-pull-3',
                    'url': reverse('users_filter', kwargs={'user_type': 'inactive'}),
                    'marked': self.user_type == 'inactive',
                    'show': self.request.user.is_superuser
                }]
            }

class UserUpdateView(UpdateView):
    form_class = forms.UserForm
    model = User

    def dispatch(self, *args, **kwargs):
        obj = get_object_or_404(User, username=kwargs['username'])
        if not self.request.user.is_superuser and self.request.user != obj:
            raise PermissionDenied
        self.object = obj
        return super(UserUpdateView, self).dispatch(*args, **kwargs)

    def get_form_kwargs(self, *args, **kwargs):
        kwargs['instance'] = self.object
        kwargs['request'] = self.request
        if self.request.POST:
            kwargs['data'] = self.request.POST
        return kwargs

    def get_object(self, *args, **kwargs):
        return get_object_or_404(User, username=self.kwargs.get('username', None))

    def get_context_data(self, *args, **kwargs):
        context = super(UserUpdateView, self).get_context_data(**kwargs)
        context['site_title'] = '%s | %s' % (self.object.username, _('Update user'))
        context['profile'] = self.object
        context['info'] = self.get_info()
        return context

    def form_valid(self, form):
        """
        Checks for the given fields and changes the user object accordingly.
        Not nice, perhaps, some permissions handling are required here.
        """
        user = get_object_or_404(User, id=form.cleaned_data['user_id'])
        _form = form.save(commit=False)
        if not self.request.user.is_superuser and (self.request.user != user or _form.is_superuser):
            raise PermissionDenied
        user.email = _form.email
        user.first_name = _form.first_name
        user.last_name = _form.username
        user.is_superuser = _form.is_superuser
        user.save()
        label = '<span class="label success radius">%s</span>' % user.username
        messages.success(self.request, mark_safe(_('User information for %s was updated.') % label))
        return HttpResponseRedirect(reverse('user', kwargs={'username': user.username}))

    def get_info(self):
        return {
            'icon': 'torso',
            'icon_url': reverse('home'),
            'title': _('Update user: %s' % self.object.username),
            'show': True,
            'buttons': user_buttons(self.request, self.object)
        }

class UserPasswordUpdateView(FormView):
    form_class = forms.UserPasswordForm
    template_name = '_update_user_password.html'

    def get_object(self, *args, **kwargs):
        return get_object_or_404(User, username=self.kwargs.get('username', None))

    def get_context_data(self, *args, **kwargs):
        self.object = self.get_object()
        context = super(UserPasswordUpdateView, self).get_context_data(**kwargs)
        context['site_title'] = '%s | %s' % (self.object.username, _('Update user password'))
        context['info'] = self.get_info()
        return context

    def form_valid(self, form):
        """
        Updates the user password according to current password and two inputs
        of the new password.
        """
        self.object = self.get_object()
        if not self.object.check_password(self.request.POST['password']):
            form._errors.setdefault('password', ErrorList())
            form._errors['password'].append(_('Wrong password.'))
            return render(self.request, '_update_userpassword.html', {'form': form})
        self.object.set_password(self.request.POST['password1'])
        self.object.save()
        label = '<span class="label radius success">%s</span>' % self.object.username
        messages.success(self.request, mark_safe(_('The password for %s was updated.') % label))
        return HttpResponseRedirect(reverse('user', kwargs={'username': self.object.username}))

    def get_info(self):
        return {
            'icon': 'torso',
            'icon_url': reverse('home'),
            'title': _('Update user: %s' % self.object.username),
            'show': True,
            'buttons': user_buttons(self.request, self.object)
        }

class UserResendInvitationView(RedirectView):
    """
    Resends an invitation to an user.
    """
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        """
        Resends invitation to user.
        """
        if not self.request.user.is_superuser:
            raise PermissionDenied
        user = get_object_or_404(User, username=kwargs['username'])

        # won't send if user is in 'invitation' status
        self.send_invitation()

        return self.request.META.get('HTTP_REFERER', reverse('users'))

class UserInactivateView(SuperUserRequiredMixin, RedirectView):
    """
    Marks a user as inactive.
    """
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        """
        Inactivates a user.
        """
        if not self.request.user.is_superuser:
            raise PermissionDenied
        user = get_object_or_404(User, username=kwargs['username'])
        if user.is_superuser:
            raise Http404
        _r = self.request.META.get('HTTP_REFERER', reverse('users'))

        # invitation
        Invitation.objects.filter(user=user).delete()

        # confirmed user
        user.first_name = 'u%d' % user.id
        user.is_active = False
        user.is_staff = False
        user.save()

        label = '<span class="label radius alert">%s</span>' % user.username
        messages.warning(self.request, mark_safe(_('The user %s was inactivated.') % label))
        return _r

class UserActivateView(SuperUserRequiredMixin, RedirectView):
    """
    Marks a user as active.
    """
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        """
        Activates a user.
        """
        if not self.request.user.is_superuser:
            raise PermissionDenied

        user = get_object_or_404(User, username=kwargs['username'])
        user.username = user.last_name
        user.first_name = user.last_name
        user.is_active = True
        user.is_staff = True
        user.save()

        label = '<span class="label radius success">%s</span>' % user.last_name
        messages.success(self.request, mark_safe(_('The user %s was activated.') % label))
        return self.request.META.get('HTTP_REFERER', reverse('users'))

#
# }}} Activity {{{
#

def activity_buttons(request):
    return [{
        'icon': 'asterisk',
        'title': _('Sitewide activity'),
        'url': reverse('activity'),
        'marked': request.resolver_match.url_name.startswith('activity'),
        'show': True
    },{
        'icon': 'torso',
        'title': _('User activity'),
        'url': reverse('user', kwargs={'username': request.user.username}),
        'marked': request.resolver_match.url_name == 'user',
        'show': True
    }]

class ActivityView(LoginRequiredMixin, TemplateView):
    template_name = '_single_activity.html'

    def dispatch(self, *args, **kwargs):
        pk = self.kwargs.get('pk', None)
        if pk:
            self.problem = get_object_or_404(models.Problem, id=pk) if pk else None
            if not perms.problem(self.request.user, 'view', self.problem):
                raise PermissionDenied
        return super(ActivityView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(ActivityView, self).get_context_data(**kwargs)
        self.url_name = self.request.resolver_match.url_name

        # Set content type
        _c = {
            'problems': 'problem', 'description': 'problem', 'problem': 'problem',
            'criteria': 'criteria',
            'idea': 'idea', 'ideas': 'idea',
            'alternatives': 'alternative', 'alternative': 'alternative',
            'comments': 'comment', 'comment': 'comment' }
        c = _c.get(self.kwargs.get('content_type', 'problem'), 'problem')
        _content_type = utils.get_object_or_none(ContentType, name=c)
        self.content_type = _content_type

        # Activities
        if self.url_name in ['activity', 'activity_short']:
            self.title = _('Activity')
            activities = Action.objects.actor(self.request.user)
            context['tabs'] = self.get_tabs()
        elif self.url_name == 'activity_objects':
            self.title = _('Activity')
            activities = Action.objects.public(action_object_content_type=_content_type)
            context['tabs'] = self.get_tabs()
        elif self.url_name == 'activity_problem':
            self.title = self.problem.title
            activities = Action.objects.target(self.problem)
            context['tabs'] = self.get_problem_tabs()
            context['problem'] = self.problem
        elif self.url_name == 'activity_problem_objects':
            self.title = _('Problem activity: %s' % self.problem.title)
            activities = Action.objects.public(action_object_content_type=_content_type, target_object_id=self.problem.id)
            context['tabs'] = self.get_problem_tabs()
            context['problem'] = self.problem
        context['activities'] = Paginator(activities, 25).page(self.request.GET.get('page', 1))
        context['activity_count'] = activities.count()

        context['info'] = self.get_info()
        context['site_title'] = '%s | %s' % (_('Activity'), utils.get_option('site_title'))
        for a in context['activities']:
            a.action_object.get_data() if callable(getattr(self, 'get_data', None)) else None
        if hasattr(self, 'problem'):
            context['criteria_count'] = models.Criteria.objects.filter(problem=self.problem).count()
            context['idea_count'] = models.Idea.objects.filter(problem=self.problem, published=True).count()
            context['alternative_count'] = models.Alternative.objects.filter(problem=self.problem).count()
            context['comment_count'] = models.Comment.objects.filter(Q(problem=self.problem) | Q(criteria__problem=self.problem) | \
                Q(idea__problem=self.problem) | Q(alternative__problem=self.problem)).count()
        else:
            context['problem_count'] = models.Problem.objects.filter(published=True).count()
            context['idea_count'] = models.Idea.objects.filter(published=True).count()
            context['comment_count'] = models.Comment.objects.all().count()
        return context

    def get_info(self):
        if self.url_name in ['activity_problem', 'activity_problem_objects']:
            p = ProblemMixin()
            p.request = self.request
            p.problem = self.problem
            p.title = self.title
            return p.get_info()
        else:
            return {
                'icon': 'list',
                'icon_url': reverse('activity'),
                'title': _('Sitewide activity'),
                'buttons': activity_buttons(self.request),
                'show': True
            }

    def get_tabs(self):
        return {
            'classes': 'activity-tabs',
            'items': [{
                    'icon': 'asterisk', 'name': _('All'),
                    'classes': 'small-12 medium-2',
                    'url': reverse('activity'),
                    'marked': self.url_name == 'activity',
                    'show': True
                },{
                    'icon': 'info', 'name': _('Problems'),
                    'classes': 'small-12 medium-2',
                    'url': reverse('activity_objects', kwargs={'content_type': 'problems'}),
                    'marked': self.url_name == 'activity_objects' and self.content_type.name == 'problem',
                    'show': True
                },{
                    'icon': 'target-two', 'name': _('Criteria'),
                    'classes': 'small-12 medium-2',
                    'url': reverse('activity_objects', kwargs={'content_type': 'criteria'}),
                    'marked': self.url_name == 'activity_objects' and self.content_type.name == 'criteria',
                    'show': True
                },{
                    'icon': 'lightbulb', 'name': _('Ideas'),
                    'classes': 'small-12 medium-2',
                    'url': reverse('activity_objects', kwargs={'content_type': 'ideas'}),
                    'marked': self.content_type.name == 'idea',
                    'show': True
                },{
                    'icon': 'list', 'name': _('Alternatives'),
                    'classes': 'small-12 medium-2',
                    'url': reverse('activity_objects', kwargs={'content_type': 'alternatives'}),
                    'marked': self.content_type.name == 'alternative',
                    'show': True
                },{
                    'icon': 'list', 'name': _('Comments'),
                    'classes': 'small-12 medium-2',
                    'url': reverse('activity_objects', kwargs={'content_type': 'comments'}),
                    'marked': self.content_type.name == 'comment',
                    'show': True
                }]
            }

    def get_problem_tabs(self):
        return {
            'items': [{
                    'icon': 'asterisk', 'name': _('All'),
                    'classes': 'small-12 medium-2 medium-offset-1',
                    'url': reverse('activity_problem', kwargs={'pk': self.problem.id}),
                    'marked': self.url_name == 'activity_problem',
                    'show': True
                },{
                    'icon': 'info', 'name': _('Description'),
                    'classes': 'small-12 medium-2',
                    'url': reverse('activity_problem_objects', kwargs={'pk': self.problem.id, 'content_type': 'description'}),
                    'marked': self.url_name == 'activity_problem_objects' and self.content_type.name == 'problem',
                    'show': True
                },{
                    'icon': 'lightbulb', 'name': _('Ideas'),
                    'classes': 'small-12 medium-2',
                    'url': reverse('activity_problem_objects', kwargs={'pk': self.problem.id, 'content_type': 'ideas'}),
                    'marked': self.content_type.name == 'idea',
                    'show': True
                },{
                    'icon': 'list', 'name': _('Alternatives'),
                    'classes': 'small-12 medium-2',
                    'url': reverse('activity_problem_objects', kwargs={'pk': self.problem.id, 'content_type': 'alternatives'}),
                    'marked': self.content_type.name == 'alternative',
                    'show': True
                },{
                    'icon': 'list', 'name': _('Comments'),
                    'classes': 'small-12 medium-2 medium-pull-1',
                    'url': reverse('activity_problem_objects', kwargs={'pk': self.problem.id, 'content_type': 'comments'}),
                    'marked': self.content_type.name == 'comment',
                    'show': True
                }]
            }

#
# }}} Problem {{{
#

class ProblemMixin(SingleObjectTemplateResponseMixin):

    def get_object(self):
        """
        Object caching.
        """
        if not hasattr(self, '_object'):
            self._object = super(ProblemMixin, self).get_object()
        if not hasattr(self, 'problem'):
            if self._object.__class__.__name__ == 'Problem':
                self.problem = self._object
            else:
                self.problem = self._object.problem
        return self._object

    def get_success_url(self, *args, **kwargs):
        return reverse('problem', kwargs={'pk': self.problem.id, 'slug': self.problem.slug})

    def dispatch(self, *args, **kwargs):
        """
        Problem permission check.
        """
        self.object = self.get_object() # cached
        if getattr(perms, self.object.__class__.__name__.lower())(self.request.user, getattr(self, 'permission', 'view'), self.object):
            return super(ProblemMixin, self).dispatch(*args, **kwargs)
        raise PermissionDenied

    def get_context_data(self, *args, **kwargs):
        context = super(ProblemMixin, self).get_context_data(*args, **kwargs)
        context['site_title'] = '%s | %s' % (self.problem.title, self.title)
        context['title'] = self.title
        context['tabs'] = self.get_tabs() if getattr(self, 'tabs', None) else None
        context['info'] = self.get_info()
        context['problem'] = self.problem
        return context

    def get_tabs(self):
        """
        Information for content tabs.
        """
        return {
            'classes': 'problem-tabs',
            'items': [{
                'icon': 'info', 'name': _('Problem'),
                'classes': 'problem-tab-selector small-12 medium-2 medium-offset-1',
                'data': 'description',
                'show': True
            },{
                'icon': 'target-two', 'name': _('Criteria'),
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

    def get_title(self):
        return self.title

    def get_info(self):
        """
        Information for the title bar.
        """
        return {
            'icon': getattr(self, 'icon', 'info'),
            'icon_url': reverse('problem', kwargs={'pk': self.problem.id, 'slug': self.problem.slug}),
            'title': self.get_title(),
            'title_url': self.problem.get_absolute_url(),
            'show': perms.problem(self.request.user, 'view', self.problem),
            'buttons': [{
                'icon': 'comments',
                'title': _('Discussion') if self.problem.published else _('Draft'),
                'url': reverse('problem', kwargs={'pk': self.problem.id, 'slug':self.problem.slug}),
                'marked': self.request.resolver_match.url_name == 'problem',
                'show': True
            },{
                'icon': 'list',
                'title': _('Activity'),
                'url': reverse('activity_problem', kwargs={'pk': self.problem.id }),
                'marked': self.request.resolver_match.url_name in ['activity_problem', 'activity_problem_objects', 'activity_problem_object'],
                'show': self.request.user.is_authenticated(),
            },{
                'icon': 'torso',
                'title': _('Contributors and permissions') if perms.problem(self.request.user, 'manage', self.problem) else _('Contributors'),
                'url': reverse('problem_collaborators', kwargs={'pk': self.problem.id}),
                'marked': self.request.resolver_match.url_name == 'problem_collaborators',
                'show': True
            }]
        }

class ProblemCreateView(RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        """
        Creates a draft problem for the user to start edition.
        """
        if perms.problem(self.request.user, 'create'):
            problem = models.Problem.objects.create(
                slug=''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(100)),
                published=False,
                open=False,
                public=False,
                author=self.request.user)
            return reverse('problem_update', kwargs={'pk': problem.id})
        raise PermissionDenied

class ProblemUpdateView(ProblemMixin, UpdateView):
    title = _('Edit problem')
    template_name = '_update_problem.html'
    form_class = forms.ProblemForm
    model = models.Problem
    permission = 'update'

    def get_title(self):
        return self.object.title

    def form_valid(self, form):
        """
        Save the object, clear the criteria and add the submitted ones in
        ``request.POST``.
        """
        self.request.user = get_user(self.request)
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
        # Coauthors
        if self.object.author.id != self.request.user.id:
            self.object.coauthor.add(self.request.user)
            # TODO follow
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
            utils.activity_register(self.request.user, self.object)
        return HttpResponseRedirect(reverse(view, kwargs=kwargs))


class ProblemCollaboratorsView(ProblemMixin, FormView):
    title = _('Problem collaborators')
    template_name = '_update_problem_collaborators.html'
    form_class = forms.ProblemCollaboratorsForm
    model = models.Problem
    permission = 'manage'

    def get_title(self):
        return self.object.title

    def get_object(self):
        if not hasattr(self, '_object'):
            self._object = get_object_or_404(models.Problem, id=self.kwargs['pk'])
            self.problem = self._object
        return self._object

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super(ProblemCollaboratorsView, self).get_form_kwargs(*args, **kwargs)
        kwargs['problem'] = self.get_object()
        return kwargs

    def get_context_data(self, *args, **kwargs):
        context = super(ProblemCollaboratorsView, self).get_context_data(**kwargs)
        context['users'] = self.object.collaborator.all()
        return context

    def form_valid(self, form):
        """
        Save the collaborators and problem status.
        """
        # permissions
        if not perms.problem(self.request.user, 'manage', self.object):
            raise PermissionDenied
        # commit
        form.problem.open = form.cleaned_data.get('open', False)
        form.problem.public = form.cleaned_data.get('public', False)
        form.problem.save()
        messages.success(self.request, mark_safe(_('Permission options in the problem was successfully saved.')))
        return HttpResponseRedirect(reverse('problem', kwargs={'pk': form.problem.id, 'slug': form.problem.slug}))

class ProblemView(ProblemMixin, DetailView):
    title = _('Problem')
    template_name = '_single_problem.html'
    model = models.Problem
    tabs = True

    def get_title(self):
        return self.object.title

    def dispatch(self, *args, **kwargs):
        self.object = self.get_object()
        hasperm = perms.problem(self.request.user, 'view', self.object)
        if 'slug' not in kwargs or kwargs['slug'] != self.object.slug and hasperm:
            return HttpResponseRedirect(reverse('problem', kwargs={
                'pk': self.object.id, 'slug': self.object.slug}))
        if hasperm:
            return super(ProblemView, self).dispatch(*args, **kwargs)
        raise PermissionDenied

        if 'slug' not in kwargs or kwargs['slug'] != self.object.slug:
            return HttpResponseRedirect(reverse('problem', kwargs={'pk': self.object.id, 'slug': self.object.slug}))
        if not perms.problem(request.user, 'view', self.object):
            raise PermissionDenied
        return super(ProblemView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(ProblemView, self).get_context_data(**kwargs)
        context['title'] = self.object.title

        # Comments
        context['comments'] = models.Comment.objects.filter(problem=self.object)
        context['comment_form'] = forms.CommentForm()

        # Collaborators
        if self.request.resolver_match.url_name == 'problem_collaborators':
            context['collaborators'] = self.object.collaborators.filter(is_staff=True).order_by('first_name')
            return context

        # Criterias
        context['criteria'] = list()
        for c in models.Criteria.objects.filter(problem=self.object):
            c.problem_count = models.Problem.objects.filter(criteria=c).count()
            c.get_data(self.request.user)
            context['criteria'].append(c)
        context['criteria'] = sorted(context['criteria'], key=lambda x: (x.weight))

        # Ideas drafts
        if self.request.user.is_authenticated():
            context['ideas_drafts'] = models.Idea.objects.filter(problem=self.object.id, author=self.request.user, published=False)
            for idea in context['ideas_drafts']:
                idea.get_data(self.request.user)
            context['ideas_drafts'] = sorted(context['ideas_drafts'], key=lambda x: (x.votes, x.updated, x.created), reverse=True)

        # Ideas
        context['ideas'] = models.Idea.objects.filter(problem=self.object.id, published=True)
        for idea in context['ideas']:
            idea.get_data(self.request.user)
        context['ideas'] = sorted(context['ideas'], key=lambda x: (x.votes, x.updated, x.created), reverse=True)

        # Alternatives
        context['alternatives'] = list()
        for a in models.Alternative.objects.filter(problem=self.object):
            a.get_data(self.request.user)
            context['alternatives'].append(a)
        context['alternatives'] = sorted(context['alternatives'], key=lambda x: (x.vote_value, x.updated, x.created), reverse=True)

        # Results
        self.object.get_data(self.request.user)
        return context

class ProblemDeleteView(DeleteMixin, DeleteView):
    model = models.Problem

    def get_success_url(self, *args, **kwargs):
        messages.success(self.request, _('The problem was deleted.'))
        return reverse('home')


#
# }}} Criteria {{{
#

class CriteriaCreateView(RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        # Validation
        problem = get_object_or_404(models.Problem, id=kwargs['problem'])
        if not perms.criteria(self.request.user, 'create', problem):
            raise PermissionDenied

        # Commit
        criteria = models.Criteria.objects.create(
            problem=problem,
            author=self.request.user)
        return reverse('criteria_update', kwargs={'pk': criteria.id})

class CriteriaDeleteView(DeleteMixin, DeleteView):
    model = models.Criteria

class CriteriaUpdateView(ProblemMixin, UpdateView):
    title = _('Update criteria')
    template_name = '_update_criteria.html'
    form_class = forms.CriteriaForm
    model = models.Criteria
    permission = 'update'
    icon = 'target-two'

    def get_title(self):
        return self.object.problem.title

    def get_object(self):
        if not hasattr(self, '_object'):
            self._object = super(CriteriaUpdateView, self).get_object()
        return self._object

    @method_decorator(login_required)
    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        self.object = self.get_object()
        if not perms.criteria(self.request.user, 'update', self.object):
            raise PermissionDenied
        return super(CriteriaUpdateView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(CriteriaUpdateView, self).get_context_data(**kwargs)
        context['site_title'] = '%s | %s' % (self.object.name, _('Edit criteria'))
        context['info'] = self.get_info()
        context['title'] = _('Edit criteria for problem: %s' % self.object.problem.title)
        return context

    def form_valid(self, form):
        form.instance.save()
        if self.object.author != self.request.user:
            self.object.coauthor.add(self.request.user)
        messages.success(self.request, mark_safe(_('Criteria saved.')))
        utils.activity_register(self.request.user, form.instance)
        return HttpResponseRedirect(reverse('problem_tab_criteria', kwargs={'pk': self.object.problem.id, 'slug': self.object.problem.slug}))

class CriteriaDeleteView(DeleteMixin, DeleteView):
    model = models.Criteria

#
# }}} Idea {{{
#

class IdeaCreateView(RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        """
        Creates a draft idea for the user to start edition.
        """
        problem = get_object_or_404(models.Problem, id=kwargs['problem'])
        # Permission validation
        if not perms.idea(self.request.user, 'create', problem):
            raise PermissionDenied
        # Commit
        self.object = models.Idea.objects.create(
            problem=problem, published=False,
            author=self.request.user)
        return reverse('idea_update', kwargs={'pk': self.object.id})

class IdeaUpdateView(ProblemMixin, UpdateView):
    title = _('Idea update')
    template_name = '_update_idea.html'
    form_class = forms.IdeaForm
    model = models.Idea
    permission = 'update'
    icon = 'lightbulb'

    def get_title(self):
        return self.object.problem.title

    def form_valid(self, form, *args, **kwargs):
        """
        Validates the idea form for the ``IdeaUpdateView``.
        """
        instance = form.save(commit=False)
        if not perms.idea(self.request.user, 'update', self.object):
            raise PermissionDenied

        # base data
        self.object = form.save(commit=False)

        # if the idea is published or is a draft
        if self.request.POST.get('publish', None):
            self.object.published = True
            return_url = self.object.get_absolute_url()
        else:
            self.object.published = False
            return_url = reverse('idea_update', kwargs={'pk': self.object.id})
        if self.request.user != self.object.author:
            self.object.coauthor.add(self.request.user)
        self.object.save()

        # get list of criteria objects
        criteria = dict()
        r = re.compile('^([0-9]+)__(.+)$')
        for f in form.fields:
            _r = r.match(f)
            if not _r: continue;
            if _r.group(1) not in criteria.keys():
                criteria[_r.group(1)] = {
                    'field_name': f,
                    'object': get_object_or_404(models.Criteria, id=_r.group(1)),
                }
            criteria[_r.group(1)][_r.group(2)] = form.cleaned_data[f]

        # Specific validation rules for each type of field

        updated = list()
        for c in criteria:
            ic, created = models.IdeaCriteria.objects.get_or_create(
                idea=self.object, criteria=criteria[c]['object'],
                description=criteria[c]['description'])

            # Test for 'scale' format
            if 'value_scale' in criteria[c] and \
                (criteria[c]['value_scale'] < criteria[c]['object'].min or \
                criteria[c]['value_scale'] > criteria[c]['object'].max):
                form._errors[criteria[c]['field_name']] = ErrorList([
                    _('Provide a value within the specified range.')
                ])
            elif 'value_scale' in criteria[c]:
                ic.value_scale = criteria[c]['value_scale']

            # Values for all the rest
            else:
                k = 'value_%s' % ic.criteria.fmt
                setattr(ic, k, criteria[c][k])

            updated.append(ic)
            verb = 'created' if created else 'updated'

        # Something went wront
        if len(form._errors) > 0:
            return self.form_invalid(form)
        # Save everything if it's ok
        else:
            [ic.save() for ic in updated]

        # Delete remaining criteria
        models.IdeaCriteria.objects \
            .exclude(id__in=[ic.id for ic in updated]) \
            .filter(idea=self.object).delete()

        # Response
        if self.object.published == True:
            utils.activity_register(self.request.user, self.object)
        if not self.object.published:
            messages.success(self.request, _('Your idea was saved as a draft and will be available only for you until it is published.'))
        else:
            messages.success(self.request, _('Your idea was successfully saved.'))
        return HttpResponseRedirect(return_url)

class IdeaDeleteView(DeleteMixin, DeleteView):
    model = models.Idea

#
# }}} Alternative {{{
#

class AlternativeView(RedirectView):
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        alternative = get_object_or_404(models.AlternativeView, id=kwargs['pk'])
        return reverse('problem_alternative', kwargs={'pk':alternative.problem.id, 'slug': alternative.problem.slug, 'alternative': alternative.id})

class AlternativeCreateView(RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        # Validation
        problem = get_object_or_404(models.Problem, id=kwargs['problem'])
        if not perms.alternative(self.request.user, 'create', problem):
            raise PermissionDenied

        # Commit
        alternative = models.Alternative.objects.create(
            problem=problem,
            author=self.request.user)
        return reverse('alternative_update', kwargs={'pk': alternative.id})

class AlternativeUpdateView(ProblemMixin, UpdateView):
    title = _('Alternative update')
    template_name = '_update_alternative.html'
    form_class = forms.AlternativeForm
    model = models.Alternative
    permission = 'update'
    icon = 'list'

    def form_valid(self, form, *args, **kwargs):
        """
        Validates the alternative form for the ``AlternativeUpdateView``.
        """
        super(AlternativeUpdateView, self).form_valid(form, *args, **kwargs)
        self.object = form.save(commit=False)
        if not perms.alternative(self.request.user, 'create', self.object.problem):
            raise PermissionDenied
        ideas = models.Idea.objects.filter(id__in=self.request.POST.getlist('idea', []))
        self.object.idea.clear()
        for i in ideas:
            self.object.idea.add(i)
        self.object.save()
        if self.object.author != self.request.user:
            self.object.coauthor.add(self.request.user)
        # Response
        utils.activity_register(self.request.user, self.object)
        messages.success(self.request, _('The alternative was successfully saved.'))
        return HttpResponseRedirect(reverse('problem_tab_alternative', kwargs={'pk': self.object.problem.id, 'slug': self.object.problem.slug}))

class AlternativeDeleteView(DeleteMixin, DeleteView):
    model = models.Alternative

#
# }}}
#
