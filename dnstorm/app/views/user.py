from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse, resolve
from django.forms.util import ErrorList
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic.edit import FormView, UpdateView

from actstream.models import actor_stream

from dnstorm.app import permissions
from dnstorm.app.forms import UserForm, UserPasswordForm
from dnstorm.app.models import Problem, Idea, Comment, Option
from dnstorm.app.utils import get_option, get_object_or_none, get_user

class UserView(TemplateView):
    template_name = '_single_activity.html'

    def get_context_data(self, *args, **kwargs):
        context = super(UserView, self).get_context_data(**kwargs)
        user = get_user(kwargs['username'])
        if not user:
            raise Http404

        context['site_title'] = '%s | %s' % (user.username, _('User profile'))
        context['profile'] = user
        context['breadcrumbs'] = self.get_breadcrumbs(username=context['username'])
        activities = Paginator(actor_stream(context['profile']), 25)
        context['activities'] = activities.page(self.request.GET.get('page', 1))
        context['user_perm_manage'] = permissions.user(obj=user, user=self.request.user, mode='manage')
        return context

    def get_breadcrumbs(self, **kwargs):
        return [
            { 'title': _('Users'), 'classes': 'unavailable' },
            { 'title': kwargs['username'], 'classes': 'current' } ]

class UsersView(TemplateView):
    template_name = '_single_users.html'

    def get_context_data(self, *args, **kwargs):
        context = super(UsersView, self).get_context_data(**kwargs)
        mode = resolve(self.request.path_info).url_name

        if self.request.user.is_superuser and mode == 'users_invitations':
            users = Paginator(User.objects.filter(is_staff=False, is_active=True).order_by('username'), 32)
        elif self.request.user.is_superuser and mode == 'users_inactive':
            users = Paginator(User.objects.filter(is_active=False).order_by('username'), 32)
        else:
            users = Paginator(User.objects.filter(is_staff=True).order_by('username'), 32)
        page = self.request.GET['page'] if 'page' in self.request.GET else 1

        context['show_actions'] = True if self.request.user.is_superuser else False
        context['mode'] = mode
        context['site_title'] = '%s | %s' % (_('Users'), get_option('site_title'))
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['users'] = users.page(page)
        return context

    def get_breadcrumbs(self, **kwargs):
        return [{ 'title': _('Users'), 'classes': 'current' }]

class UserUpdateView(UpdateView):
    form_class = UserForm
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
        return self.object

    def get_context_data(self, *args, **kwargs):
        context = super(UserUpdateView, self).get_context_data(**kwargs)
        context['site_title'] = '%s | %s' % (self.object.username, _('Update user'))
        context['profile'] = self.object
        context['breadcrumbs'] = self.get_breadcrumbs()
        return context

    def get_breadcrumbs(self, **kwargs):
        return [{ 'title': _('Users'), 'classes': 'current' }]

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
        messages.success(self.request, _('User information was updated.'))
        return HttpResponseRedirect(reverse('user', kwargs={'username': user_obj.username}))

class UserPasswordUpdateView(FormView):
    form_class = UserPasswordForm
    template_name = '_update_userpassword.html'

    def dispatch(self, *args, **kwargs):
        obj = get_object_or_404(User, username=kwargs['username'])
        if not self.request.user.is_superuser and self.request.user != obj:
            raise PermissionDenied
        self.object = obj
        return super(UserPasswordUpdateView, self).dispatch(*args, **kwargs)

    def get_object(self, *args, **kwargs):
        return self.object

    def get_context_data(self, *args, **kwargs):
        context = super(UserPasswordUpdateView, self).get_context_data(**kwargs)
        context['site_title'] = '%s | %s' % (self.object.username, _('Update user password'))
        context['breadcrumbs'] = self.get_breadcrumbs()
        return context

    def get_breadcrumbs(self, **kwargs):
        return [{ 'title': _('Users'), 'classes': 'current' }]

    def form_valid(self, form):
        """
        Updates the user password according to current password and two inputs
        of the new password.
        """

        if not self.object.check_password(self.request.POST['password']):
            form._errors.setdefault('password', ErrorList())
            form._errors['password'].append(_('Wrong password.'))
            return render(self.request, '_update_userpassword.html', {'form': form})

        self.object.set_password(self.request.POST['password1'])
        self.object.save()
        messages.success(self.request, _('User password was updated.'))
        return HttpResponseRedirect(reverse('user', kwargs={'username': self.object.username}))

class UserInactivateView(RedirectView):
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
        user.first_name = 'u%d' % user.id
        user.is_active = False
        user.is_staff = False
        user.save()

        messages.warning(self.request, _('The user was inactivated.'))
        return reverse('users')

class UserActivateView(RedirectView):
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

        messages.success(self.request, _('The user was activated.'))
        return reverse('users')
