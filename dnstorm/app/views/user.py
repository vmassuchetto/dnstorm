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
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic.edit import FormView, UpdateView

from actstream.models import actor_stream

from dnstorm.app import permissions
from dnstorm.app.forms import UserForm, UserPasswordForm, CommentForm
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
        context['info'] = self.get_info()
        activities = Paginator(actor_stream(context['profile']), 25)
        context['activities'] = activities.page(self.request.GET.get('page', 1))
        context['comment_form'] = CommentForm()
        context['user_perm_manage'] = permissions.user(obj=user, user=self.request.user, mode='manage')
        return context

    def get_info(self):
        return {
            'icon': 'torso',
            'icon_url': reverse('users'),
            'title': _('Users'),
            'show': True
        }

class UsersView(TemplateView):
    template_name = '_single_users.html'

    def get_context_data(self, *args, **kwargs):
        context = super(UsersView, self).get_context_data(**kwargs)
        self.url_name = self.request.resolver_match.url_name
        self.user_type = self.kwargs.get('user_type', 'active')
        if self.user_type == 'invitations':
            users = User.objects.filter(is_active=True, is_staff=False)
        elif self.user_type == 'inactive':
            users = User.objects.filter(is_active=False, is_staff=False)
        else:
            users = User.objects.filter(is_active=True, is_staff=True)
        page = self.request.GET['page'] if 'page' in self.request.GET else 1

        context['show_actions'] = True if self.request.user.is_superuser else False
        context['user_type'] = self.user_type
        context['site_title'] = '%s | %s' % (_('Users'), get_option('site_title'))
        context['info'] = self.get_info()
        context['tabs'] = self.get_tabs()
        context['comment_form'] = CommentForm()
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
        label = '<span class="label success radius">%s</span>' % user.username
        messages.success(self.request, mark_safe(_('User information for %s was updated.') % label))
        return HttpResponseRedirect(reverse('user', kwargs={'username': user.username}))

class UserPasswordUpdateView(FormView):
    form_class = UserPasswordForm
    template_name = '_update_user_password.html'

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
        label = '<span class="label radius success">%s</span>' % self.object.username
        messages.success(self.request, mark_safe(_('The password for %s was updated.') % label))
        return HttpResponseRedirect(reverse('user', kwargs={'username': self.object.username}))

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
        _r = self.request.META.get('HTTP_REFERER', reverse('users'))

        # invitation
        if user.is_active and not user.is_staff:
            label = '<span class="label radius alert">%s</span>' % user.email
            user.delete()
            messages.warning(self.request, mark_safe(_('The invitation to %s was cancelled.') % label))
            return _r

        # confirmed user
        user.first_name = 'u%d' % user.id
        user.is_active = False
        user.is_staff = False
        user.save()

        label = '<span class="label radius alert">%s</span>' % user.last_name
        messages.warning(self.request, mark_safe(_('The user %s was inactivated.') % label))
        return _r

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

        label = '<span class="label radius success">%s</span>' % user.last_name
        messages.success(self.request, mark_safe(_('The user %s was activated.') % label))
        return self.request.META.get('HTTP_REFERER', reverse('users'))
