from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.forms.util import ErrorList
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView, UpdateView

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

        user_obj = get_object_or_404(User, id=form.cleaned_data['user_id'])
        form_obj = form.save(commit=False)
        if not self.request.user.is_superuser and (self.request.user != user_obj or form_obj.is_superuser):
            raise PermissionDenied
        user_obj.email = form_obj.email
        user_obj.first_name = form_obj.first_name
        user_obj.is_superuser = form_obj.is_superuser
        user_obj.save()
        messages.success(self.request, _('User information saved'))
        return HttpResponseRedirect(reverse('user', kwargs={'username': user_obj.username}))

class UserPasswordUpdateView(FormView):
    form_class = UserPasswordForm
    template_name = 'user_password.html'

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
            return render(self.request, 'user_password.html', {'form': form})

        self.object.set_password(self.request.POST['password1'])
        self.object.save()
        messages.success(self.request, _('User password updated'))
        return HttpResponseRedirect(reverse('user', kwargs={'username': self.object.username}))
