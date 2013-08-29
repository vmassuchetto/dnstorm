from datetime import datetime

from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect
from django.views.generic import DetailView
from django.views.generic.edit import FormView, CreateView, UpdateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from dnstorm.models import Problem
from dnstorm.forms import ProblemForm, IdeaForm

class ProblemCreateView(CreateView):
    template_name = 'problem_edit.html'
    form_class = ProblemForm
    model = Problem

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProblemCreateView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()
        return HttpResponseRedirect(reverse('problem', kwargs={'slug':self.object.slug}))

class ProblemUpdateView(UpdateView):
    template_name = 'problem_edit.html'
    form_class = ProblemForm
    model = Problem

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProblemUpdateView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()
        p = Problem.objects.get(pk=self.object.id)
        p.pk = None
        p.revision = self.object
        p.save()
        return HttpResponseRedirect(reverse('problem', kwargs={'slug':self.object.slug}))

class ProblemRevisionView(DetailView):
    template_name = 'problem_revisions.html'
    model = Problem

    def get_context_data(self, *args, **kwargs):
        context = super(ProblemRevisionView, self).get_context_data(**kwargs)
        context['revisions'] = Problem.objects.filter(revision=self.kwargs['pk']).order_by('modified')
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
        return context

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.problem = self.problem
        obj.user = self.request.user
        obj.save()
        return HttpResponseRedirect(reverse('problem', kwargs={'slug':self.problem.slug}))
