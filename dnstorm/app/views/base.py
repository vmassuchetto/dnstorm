from datetime import datetime
import urlparse

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import login as login_view
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
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import FormView, UpdateView

from actstream.actions import follow
from actstream.models import user_stream
from registration.backends.default.views import RegistrationView as BaseRegistrationView
from registration import signals as registration_signals

from dnstorm.app import permissions
from dnstorm.app.forms import OptionsForm, RegistrationForm
from dnstorm.app.utils import get_object_or_none, activity_count, get_option, update_option
from dnstorm.app.models import Option, Problem, Idea, Comment, Criteria, Alternative, Invitation

class HomeView(TemplateView):
    """
    Front landing page.
    """
    template_name = '_home.html'

    def get_context_data(self, *args, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        mode = resolve(self.request.path_info).url_name
        authenticated = self.request.user.is_authenticated()

        # problems
        if authenticated and mode == 'problems_my':
            q_problems = (Q(published=True) & Q(author=self.request.user))
        elif authenticated and mode == 'problems_drafts':
            q_problems = (Q(published=False) & Q(author=self.request.user))
        elif authenticated and mode == 'problems_contribute':
            q_problems = (Q(published=True) & Q(contributor__in=[self.request.user]) & ~Q(author=self.request.user))
        elif authenticated:
            q_problems = (Q(published=True)) & (Q(public=True) | Q(contributor__in=[self.request.user]))
        else:
             q_problems = (Q(published=True) & Q(public=True))

        context['mode'] = mode
        context['breadcrumbs'] = self.get_breadcrumbs()

        problems = Paginator(Problem.objects.filter(q_problems).distinct().order_by('-last_activity'), 25)
        context['problems'] = problems.page(self.request.GET.get('page', 1))
        return context

    def get_breadcrumbs(self):
        return [{ 'title': _('Problems'), 'classes': 'current' }]

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

        if _hash:
            invitation = get_object_or_404(Invitation, hash=_hash)
            context['problems'] = Problem.objects.filter(contributor__in=[invitation.user])

        return context

    def register(self, request, **cleaned_data):
        """
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
        pcs = Problem.objects.filter(contributor__in=[user])
        msg = _('Welcome to DNStorm. ')
        if pcs:
            msg += _('You are already a contributor of a problem:&nbsp;')
            for p in pcs:
                msg += '<a class="label success radius" href="%s">%s</a>&nbsp;' % (reverse('problem', kwargs={'pk': p.id, 'slug': p.slug}), p.title)
            _return = reverse('problems_contribute')
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

class OptionsView(FormView):
    """
    Admin options page for superusers.
    """
    template_name = '_update_options.html'
    form_class = OptionsForm

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        if not self.request.user.is_superuser:
            raise PermissionDenied()
        return super(OptionsView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(OptionsView, self).get_context_data(**kwargs)
        context['site_title'] = '%s | %s' % (_('Site options'), get_option('site_title'))
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['title'] = _('Options')
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Options'), 'classes': 'current' } ]

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

class ActivityView(TemplateView):
    template_name = '_single_activity.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        if not self.request.user.is_authenticated():
            raise PermissionDenied
        return super(ActivityView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(ActivityView, self).get_context_data(**kwargs)
        activities = Paginator(user_stream(self.request.user), 25)
        context['site_title'] = '%s | %s' % (_('Activity'), get_option('site_title'))
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['activities'] = activities.page(self.request.GET.get('page', 1))
        context['problem_count'] = Problem.objects.filter(published=True).count()
        context['criteria_count'] = Criteria.objects.all().count()
        context['idea_count'] = Idea.objects.filter(published=True).count()
        context['alternative_count'] = Alternative.objects.all().count()
        context['comment_count'] = Comment.objects.all().count()
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Activity'), 'classes': 'current' }
        ]
