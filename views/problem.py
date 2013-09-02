from datetime import datetime
from lib.diff import inline_diff

from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect
from django.views.generic import DetailView
from django.views.generic.edit import FormView, CreateView, UpdateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.html import strip_tags

import reversion

from dnstorm.models import Problem, Idea, Vote
from dnstorm.forms import ProblemForm, IdeaForm

class ProblemCreateView(CreateView):
    template_name = 'problem_edit.html'
    form_class = ProblemForm
    model = Problem

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProblemCreateView, self).dispatch(*args, **kwargs)

    @reversion.create_revision()
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.author = self.request.user
        self.object.save()
        return HttpResponseRedirect(reverse('problem', kwargs={'slug':self.object.slug}))

class ProblemUpdateView(UpdateView):
    template_name = 'problem_edit.html'
    form_class = ProblemForm
    model = Problem

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProblemUpdateView, self).dispatch(*args, **kwargs)

    @reversion.create_revision()
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.author = self.request.user
        self.object.save()
        return HttpResponseRedirect(reverse('problem', kwargs={'slug':self.object.slug}))

class ProblemRevisionView(DetailView):
    template_name = 'problem_revision.html'
    model = Problem

    def get_context_data(self, *args, **kwargs):
        context = super(ProblemRevisionView, self).get_context_data(**kwargs)
        context['revisions'] = list()
        revisions = reversion.get_for_object(self.object)
        for rev in revisions:
            r = rev.object_version.object
            context['revisions'].append({
                'title': r.title,
                'description': r.description,
                'author': r.author,
                'modified': r.modified
            })
        return context

class ProblemView(FormView):
    template_name = 'problem.html'
    form_class = IdeaForm

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        try:
            self.problem = Problem.objects.get(slug=self.kwargs['slug'])
        except Problem.DoesNotExist:
            raise Http404()
        return super(ProblemView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(ProblemView, self).get_context_data(**kwargs)
        context['problem'] = self.problem
        if self.problem.max > 0:
            context['user_ideas_left'] = self.problem.max - Idea.objects.filter(problem=self.problem, author=self.request.user).count()
        else:
            context['user_ideas_left'] = 1
        context['ideas'] = Idea.objects.filter(problem=self.problem)
        for idea in context['ideas']:
            user_vote = Vote.objects.filter(idea=idea, author=self.request.user)
            idea.user_vote = user_vote[0] if len(user_vote) else False
        return context

    @reversion.create_revision()
    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.problem = self.problem
        obj.author = self.request.user
        obj.save()
        return HttpResponseRedirect(reverse('problem', kwargs={'slug':self.problem.slug}))
