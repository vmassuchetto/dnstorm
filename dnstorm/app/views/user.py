from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import RedirectView
from django.views.generic.base import TemplateView
from django.views.generic.edit import UpdateView

from actstream.models import actor_stream

from dnstorm.app.forms import UserForm, UserPasswordForm
from dnstorm.app.models import Problem, Idea, Comment, Option
from dnstorm.app.utils import get_option, get_object_or_none

class UserView(TemplateView):
    template_name = 'activity.html'

    def get_context_data(self, *args, **kwargs):
        context = super(UserView, self).get_context_data(**kwargs)
        user = get_object_or_404(User, username=kwargs['username'], is_active=True)
        user.problem_count = Problem.objects.filter(author=user).count()
        user.idea_count = Idea.objects.filter(author=user).count()
        user.comment_count = Comment.objects.filter(author=user).count()
        context['site_title'] = '%s | %s' % (user.username, _('User profile'))
        context['profile'] = user
        context['breadcrumbs'] = self.get_breadcrumbs(username=context['username'])
        activities = Paginator(actor_stream(context['profile']), 20)
        context['activities'] = activities.page(self.request.GET.get('page', 1))
        return context

    def get_breadcrumbs(self, **kwargs):
        return [
            { 'title': _('Users'), 'classes': 'unavailable' },
            { 'title': kwargs['username'], 'classes': 'current' } ]

class UsersView(TemplateView):
    template_name = 'users.html'

    def get_context_data(self, *args, **kwargs):
        context = super(UsersView, self).get_context_data(**kwargs)
        users = Paginator(User.objects.all().order_by('username'), 100)
        page = self.request.GET['page'] if 'page' in self.request.GET else 1
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
        return {'request': self.request}

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

class UserUpdatePasswordView(UpdateView):
    form_class = UserPasswordForm
    model = User

    def dispatch(self, *args, **kwargs):
        obj = get_object_or_404(User, username=kwargs['username'])
        if not self.request.user.is_superuser and self.request.user != obj:
            raise PermissionDenied
        self.object = obj
        return super(UserUpdatePasswordView, self).dispatch(*args, **kwargs)

    def get_object(self, *args, **kwargs):
        return self.object

    def get_context_data(self, *args, **kwargs):
        context = super(UserUpdatePasswordView, self).get_context_data(**kwargs)
        context['site_title'] = '%s | %s' % (self.object.username, _('Update user password'))
        context['breadcrumbs'] = self.get_breadcrumbs()
        return context

    def get_breadcrumbs(self, **kwargs):
        return [{ 'title': _('Users'), 'classes': 'current' }]


'''class AdminUserUpdateView(UpdateView):
    template_name = 'admin_user_edit.html'
    model = User
    form_class = AdminUserForm

    def get_object(self, queryset=None):
        return get_object_or_404(User, id=self.kwargs['user_id'])

    def get_success_url(self):
        if self.request.user.is_superuser:
            return reverse('admin_user')
        return reverse('admin_user', {'user_id': self.request.user.id})

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        if self.request.user.is_superuser or self.request.user == self.object:
            return super(AdminUserUpdateView, self).dispatch(*args, **kwargs)
        raise PermissionDenied

    def get_context_data(self, *args, **kwargs):
        context = super(AdminUserUpdateView, self).get_context_data(**kwargs)
        context['admin_user'] = get_object_or_404(User, id=self.kwargs['user_id'])
        _user = Option().get('_user_backup_' + str(context['admin_user'].id))
        context['bkp_admin_user'] = pickle.loads(str(_user)) if _user else None
        context['breadcrumbs'] = self.get_breadcrumbs(username=context['admin_user'].username, user_id=self.kwargs['user_id'])
        return context

    def get_breadcrumbs(self, **kwargs):
        return [
            { 'title': _('Admin'), 'classes': 'unavailable' },
            { 'title': _('Users'), 'url': reverse('admin_user') },
            { 'title': kwargs['username'], 'url': reverse('admin_user_edit', kwargs={'user_id': kwargs['user_id']}) } ]

class AdminUserActivateView(RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        if not self.request.user.is_superuser:
            raise PermissionDenied
        user = get_object_or_404(User, id=self.kwargs['user_id'])
        userdata = Option().get('_user_backup_' + str(user.id))
        if userdata:
            _user = pickle.loads(str(userdata))
            user = _user
            _user.delete()
        user.is_active = True
        user.save()
        return reverse('admin_user_edit', kwargs={'user_id': user.id})

class AdminUserDeactivateView(RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        if not self.request.user.is_superuser:
            raise PermissionDenied
        user = get_object_or_404(User, id=self.kwargs['user_id'])
        if self.request.user.is_superuser and self.request.user == user:
            raise PermissionDenied
        Option().get_or_create(name='_user_backup_' + str(user.id), value=pickle.dumps(user)).save()
        user.is_active = False
        user.email = 'user%d@dnstorm' % user.id
        user.username = 'user%d' % user.id
        user.first_name = ''
        user.last_name = ''
        user.save()
        return reverse('admin_user_edit', kwargs={'user_id': user.id})'''
