from django.contrib.auth.models import User
from django.views.generic import DetailView
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator

from dnstorm.models import Option, Problem, Idea, Comment, ActivityManager
from dnstorm.forms import OptionsForm, AccountCreateForm

class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, *args, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        problems = Paginator(Problem.objects.all(), 25)
        page = self.request.GET['page'] if 'page' in self.request.GET else 1
        context['problems'] = problems.page(page)
        context['problems_total'] = Problem.objects.all().count()
        return context

class OptionsView(FormView):
    template_name = 'options.html'
    form_class = OptionsForm

    def get_context_data(self, *args, **kwargs):
        context = super(OptionsView, self).get_context_data(**kwargs)
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['title'] = _('Options')
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Options'), 'classes': 'current' } ]

class UserView(TemplateView):
    template_name = 'user.html'

    def get_context_data(self, *args, **kwargs):
        context = super(UserView, self).get_context_data(**kwargs)
        self.user = get_object_or_404(User, username=kwargs['username'])
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['user'] = self.user
        context['problem_count'] = Problem.objects.filter(author=self.user).count()
        context['idea_count'] = Idea.objects.filter(author=self.user).count()
        context['comment_count'] = Comment.objects.filter(author=self.user).count()
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Users'), 'classes': 'unavailable' },
            { 'title': self.user.username, 'classes': 'current' } ]

class CommentView(RedirectView):
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        comment = get_object_or_404(Comment, id=kwargs['pk'])
        problem = comment.problem if comment.problem else comment.idea.problem
        return reverse('problem', kwargs={'slug':problem.slug}) + '#comment-' + str(comment.id)

class ActivityView(TemplateView):
    template_name = 'activity.html'

    def get_context_data(self, *args, **kwargs):
        context = super(ActivityView, self).get_context_data(**kwargs)
        context['activities'] = ActivityManager().get(limit=20)
        return context
