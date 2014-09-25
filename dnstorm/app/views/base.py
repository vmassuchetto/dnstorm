import urlparse

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import login
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import Http404, HttpResponseRedirect, QueryDict
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import DetailView, RedirectView
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import FormView, UpdateView

from actstream.actions import follow
from actstream.models import user_stream
from registration.backends.default.views import RegistrationView as BaseRegistrationView
from registration import signals as registration_signals

from dnstorm.app import permissions
from dnstorm.app.forms import AdminOptionsForm, RegistrationForm
from dnstorm.app.utils import get_object_or_none, activity_count, get_option, update_option
from dnstorm.app.models import Option, Problem, Idea, Comment, Criteria, Invitation

class HomeView(TemplateView):
    """
    Default landing page.
    """
    template_name = 'home.html'

    def get_context_data(self, *args, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        if self.request.user.is_superuser:
            q_problems = Q()
        elif self.request.user.is_authenticated():
            q_problems = Q(public=True) | Q(author=self.request.user.id) | Q(contributor=self.request.user.id)
        else:
            q_problems = Q(public=True)
        first_time = get_option('firsttime_homeview')
        if not first_time:
            context['first_time'] = True
            #update_option('firsttime_homeview', True)
        context['breadcrumbs'] = self.get_breadcrumbs()
        problems = Paginator(Problem.objects.filter(q_problems).distinct().order_by('-last_activity'), 25)
        context['problems'] = problems.page(self.request.GET.get('page', 1))
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Problems'), 'classes': 'current' } ]

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
            context['problems'] = [i.problem for i in Invitation.objects.filter(email=invitation.email)]

        return context

    def register(self, request, **cleaned_data):
        """
        Register the user without an activation link and add it as a
        contributor of the problems with pending invitations.
        """

        # Create user

        username, email, password = cleaned_data['username'], cleaned_data['email'], cleaned_data['password1']
        new_user = User.objects.create(username=username, email=email, password=password, is_staff=True)

        # Invitations

        _hash = request.POST.get('hash', None)
        invitation = get_object_or_none(Invitation, hash=_hash) if _hash else None
        if invitation:
            for i in Invitation.objects.filter(email=invitation.email):
                i.problem.contributor.add(new_user)
                follow(new_user, i.problem, actor_only=False)
                activity_count(i.problem)
                i.delete()
            invitation.delete()

        # Auto-login via signaly handler

        registration_signals.user_registered.send(sender=self.__class__, user=new_user, request=request)
        return new_user

class AdminOptionsView(FormView):
    """
    Admin options page for superusers.
    """
    template_name = 'admin_options.html'
    form_class = AdminOptionsForm

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        if not self.request.user.is_superuser:
            raise PermissionDenied()
        return super(AdminOptionsView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(AdminOptionsView, self).get_context_data(**kwargs)
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

        return HttpResponseRedirect(reverse('admin_options'))

class CommentView(RedirectView):
    """
    Redirects to the '#comment-<id>' URL in a problem.
    """
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        comment = get_object_or_404(Comment, id=kwargs['pk'])
        problem = comment.problem if comment.problem else comment.idea.problem
        return reverse('problem', kwargs={'slug':problem.slug}) + '#comment-' + str(comment.id)

class CriteriasView(TemplateView):
    template_name = 'criteria.html'

    def get_context_data(self, *args, **kwargs):
        context = super(CriteriasView, self).get_context_data(**kwargs)
        criterias = Paginator(Criteria.objects.all().order_by('name'), 21)
        context['site_title'] = '%s | %s' % (_('Criterias'), get_option('site_title'))
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['criterias'] = criterias.page(self.request.GET.get('page', 1))
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Criterias'), 'classes': 'current' }
        ]

class CriteriaView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, *args, **kwargs):
        context = super(CriteriaView, self).get_context_data(**kwargs)
        self.criteria = get_object_or_404(Criteria, slug=kwargs['slug'])
        problems = Paginator(Problem.objects.filter(criteria=self.criteria).distinct().order_by('-last_activity'), 25)
        context['site_title'] = '%s | %s' % (self.criteria.name, _('Criteria problems'))
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['problems'] = problems.page(self.request.GET.get('page', 1))
        context['criteria'] = self.criteria
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Criterias'), 'url': reverse('criterias') },
            { 'title': self.criteria.name, 'classes': 'current' }
        ]

class ActivityView(TemplateView):
    template_name = 'activity.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        if not self.request.user.is_authenticated():
            raise PermissionDenied
        return super(ActivityView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(ActivityView, self).get_context_data(**kwargs)
        activities = Paginator(user_stream(self.request.user), 20)
        context['site_title'] = '%s | %s' % (_('Activity'), get_option('site_title'))
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['activities'] = activities.page(self.request.GET.get('page', 1))
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Activity'), 'classes': 'current' }
        ]

class LoginView(View):
    """
    Redirects valid users to the home page instead of showing the login form.
    """

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated():
            next = self.request.GET.get('next', None)
            next = next if next else reverse('home')
            return HttpResponseRedirect(next)
        else:
            return login(self.request)

    def post(self, *args, **kwargs):
        return self.get(*args, **kwargs)
