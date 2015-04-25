from datetime import datetime
import urlparse

from django.contrib import messages
from django.contrib.auth import authenticate, login, get_user
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import login as login_view
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse, resolve
from django.db.models import Q
from django.http import Http404, HttpResponseRedirect, QueryDict
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.views.generic import DetailView, RedirectView
from django.views.generic.base import TemplateView, View, TemplateResponseMixin
from django.views.generic.edit import FormView, UpdateView

from actstream.actions import follow
from actstream.models import Action

from registration.backends.default.views import RegistrationView as BaseRegistrationView
from registration import signals as registration_signals

from dnstorm.app import permissions
from dnstorm.app.forms import OptionsForm, RegistrationForm, CommentForm
from dnstorm.app.utils import get_object_or_none, activity_count, get_option, update_option
from dnstorm.app.models import Option, Problem, Idea, Comment, Criteria, Alternative, Invitation
from dnstorm.app.views.problem import problem_buttons

class LoginRequiredMixin(TemplateResponseMixin):

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return self.handle_no_permission(request)
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)

class SuperUserRequiredMixin(TemplateResponseMixin):

    def dispatch(self, *args, **kwargs):
        self.request.user = get_user(self.request)
        if not self.request.user.is_superuser:
            raise PermissionDenied()
        return super(SuperUserRequiredMixin, self).dispatch(*args, **kwargs)

class HomeView(TemplateView):
    """
    Front landing page.
    """
    template_name = '_home.html'

    def get_context_data(self, *args, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        self.request.user = get_user(self.request)
        authenticated = self.request.user.is_authenticated()

        # problems
        if authenticated and self.request.resolver_match.url_name == 'problems_my':
            q_problems = (Q(published=True) & Q(author=self.request.user))
        elif authenticated and self.request.resolver_match.url_name == 'problems_drafts':
            q_problems = (Q(published=False) & Q(author=self.request.user))
        elif authenticated and self.request.resolver_match.url_name == 'problems_contribute':
            q_problems = (Q(collaborator__in=[self.request.user]) & ~Q(author=self.request.user))
        elif self.request.user.is_superuser:
            q_problems = (~Q(collaborator__in=[self.request.user]) & ~Q(author=self.request.user))
        else:
            q_problems = (Q(published=True, public=True))

        if authenticated:
            context['tabs'] = self.get_tabs()
        problems = Paginator(Problem.objects.filter(q_problems).distinct().order_by('-last_activity'), 25)
        context['problems'] = problems.page(self.request.GET.get('page', 1))
        context['info'] = self.get_info()
        if not problems.count and self.request.resolver_match.url_name == 'home':
            context['body_class'] = 'show-help'
        return context

    def get_info(self):
        return {
            'icon': 'target-two',
            'title': _('Problems')
        }

    def get_tabs(self):
        return {
            'items': [{
                    'icon': 'web' if not self.request.user.is_superuser else 'asterisk',
                    'name': _('Open problems') if not self.request.user.is_superuser else _('All problems'),
                    'classes': 'small-12 medium-2 medium-offset-2',
                    'url': reverse('home'),
                    'marked': self.request.resolver_match.url_name == 'home',
                    'show': True
                },{
                    'icon': 'target-two', 'name': _('Managed by me'),
                    'classes': 'small-12 medium-2',
                    'url': reverse('problems_my'),
                    'marked': self.request.resolver_match.url_name == 'problems_my',
                    'show': True
                },{
                    'icon': 'page-edit', 'name': _('Drafts'),
                    'classes': 'small-12 medium-2',
                    'url': reverse('problems_drafts'),
                    'marked': self.request.resolver_match.url_name == 'problems_drafts',
                    'show': True
                },{
                    'icon': 'lightbulb', 'name': _('Contributing'),
                    'classes': 'small-12 medium-2 medium-pull-2',
                    'url': reverse('problems_collaborating'),
                    'marked': self.request.resolver_match.url_name == 'problems_collaborating',
                    'show': True
                }]
            }

class RegistrationView(BaseRegistrationView):
    form_class = RegistrationForm

    def get_context_data(self, *args, **kwargs):
        """
        Display all the problems the user will gain access to contribution if a
        valid hash is provided with the registration link.
        """
        context = super(RegistrationView, self).get_context_data()
        context['site_title'] = '%s | %s' % (_('Register'), get_option('site_title'))

        _hash = self.request.GET.get('hash', self.request.POST.get('hash', None))
        try:
            _hash = int(_hash)
        except:
            None
        if self.request.POST:
            context['form'] = RegistrationForm(self.request.POST)
        elif _hash:
            context['form'] = RegistrationForm(hash=_hash)
        else:
            context['form'] = RegistrationForm()
        context['info'] = self.get_info()

        if _hash:
            invitation = get_object_or_404(Invitation, hash=_hash)
            context['problems'] = Problem.objects.filter(collaborator__in=[invitation.user])

        return context

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
            invitation = get_object_or_404(Invitation, hash=_hash)
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
            return _user

        # Delete invitations
        for i in Invitation.objects.filter(user=user):
            i.delete()

        # Welcome message
        pcs = Problem.objects.filter(collaborator__in=[user])
        msg = _('Welcome to DNStorm. ')
        if pcs:
            msg += _('You are already a collaborator of a problem:&nbsp;')
            for p in pcs:
                msg += '<a class="label success radius" href="%s">%s</a>&nbsp;' % (reverse('problem', kwargs={'pk': p.id, 'slug': p.slug}), p.title)
            _return = reverse('problems_collaborating')
        else:
            msg += _('You can start by creating a new problem or contrubuting to existing ones.')
            _return = reverse('home')
        messages.success(self.request, mark_safe(msg))

        # Log in
        _user = authenticate(username=cleaned_data['username'], password=cleaned_data['password1'])
        login(self.request, _user)

        # Response
        return HttpResponseRedirect(_return)

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

class OptionsView(SuperUserRequiredMixin, FormView):
    """
    Admin options page for superusers.
    """
    template_name = '_update_options.html'
    form_class = OptionsForm

    def get_context_data(self, *args, **kwargs):
        context = super(OptionsView, self).get_context_data(**kwargs)
        context['site_title'] = '%s | %s' % (_('Site options'), get_option('site_title'))
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
            update_option(name, form.cleaned_data[name])

        # Update Django site framework

        url = urlparse.urlparse(form.cleaned_data['site_url'])
        update_option('scheme', url.scheme)
        s = Site.objects.get(id=1)
        s.name = form.cleaned_data['site_title']
        s.domain = url.netloc
        s.save()

        messages.success(self.request, mark_safe(_('Options saved.')))
        return HttpResponseRedirect(reverse('options'))

class CommentView(RedirectView):
    """
    Redirects to the '#comment-<id>' URL in a problem.
    """
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        comment = get_object_or_404(Comment, id=kwargs['pk'])
        problem = comment.problem if comment.problem else comment.idea.problem
        return reverse('problem', kwargs={'pk': problem.id, 'slug':problem.slug}) + '#comment-' + str(comment.id)

class ActivityView(LoginRequiredMixin, TemplateView):
    template_name = '_single_activity.html'

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
        _content_type = get_object_or_none(ContentType, name=c)
        self.content_type = _content_type
        if self.kwargs.get('pk', None):
            self.problem = get_object_or_404(Problem, id=self.kwargs.get('pk', None))

        # Activities
        if self.url_name in ['activity', 'activity_short']:
            activities = Action.objects.actor(self.request.user)
            context['tabs'] = self.get_tabs()
        elif self.url_name == 'activity_objects':
            activities = Action.objects.public(action_object_content_type=_content_type)
            context['tabs'] = self.get_tabs()
        elif self.url_name == 'activity_problem':
            activities = Action.objects.target(self.problem)
            context['tabs'] = self.get_problem_tabs()
            context['problem'] = self.problem
        elif self.url_name == 'activity_problem_objects':
            activities = Action.objects.public(action_object_content_type=_content_type, target_object_id=self.problem.id)
            context['tabs'] = self.get_problem_tabs()
            context['problem'] = self.problem
        activities = Paginator(activities, 25)
        context['activities'] = activities.page(self.request.GET.get('page', 1))

        context['info'] = self.get_info()
        context['site_title'] = '%s | %s' % (_('Activity'), get_option('site_title'))
        for a in context['activities']:
            a.action_object.fill_data() if callable(getattr(self, 'fill_data', None)) else None
        if hasattr(self, 'problem'):
            context['criteria_count'] = Criteria.objects.filter(problem=self.problem).count()
            context['idea_count'] = Idea.objects.filter(problem=self.problem, published=True).count()
            context['alternative_count'] = Alternative.objects.filter(problem=self.problem).count()
            context['comment_count'] = Comment.objects.filter(Q(problem=self.problem) | Q(criteria__problem=self.problem) | \
                Q(idea__problem=self.problem) | Q(alternative__problem=self.problem)).count()
        else:
            context['problem_count'] = Problem.objects.filter(published=True).count()
            context['idea_count'] = Idea.objects.filter(published=True).count()
            context['comment_count'] = Comment.objects.all().count()
        return context

    def get_info(self):
        if self.url_name in ['activity_problem', 'activity_problem_objects']:
            return {
                'icon': 'target-two',
                'icon_url': reverse('problem', kwargs={'pk': self.problem.id, 'slug': self.problem.slug}),
                'title': _('Problem activity: %s' % self.problem.title),
                'title_url': self.problem.get_absolute_url(),
                'buttons': problem_buttons(self.request, self.problem),
                'status': 'public' if self.problem.public else 'private',
                'show': True
            }
        else:
            return {
                'icon': 'list',
                'icon_url': reverse('activity'),
                'title': _('Sitewide activity'),
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
                    'icon': 'target-two', 'name': _('Problems'),
                    'classes': 'small-12 medium-2',
                    'url': reverse('activity_objects', kwargs={'content_type': 'problems'}),
                    'marked': self.url_name == 'activity_objects' and self.content_type.name == 'problem',
                    'show': True
                },{
                    'icon': 'cloud', 'name': _('Criteria'),
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
                    'icon': 'target-two', 'name': _('Description'),
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
