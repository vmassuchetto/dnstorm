from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView
from django.views.generic.edit import UpdateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from dnstorm.models import Problem, Idea
from dnstorm.forms import IdeaForm

import reversion

class IdeaUpdateView(UpdateView):
    template_name = 'idea_edit.html'
    form_class = IdeaForm
    model = Idea

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(IdeaUpdateView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(IdeaUpdateView, self).get_context_data(**kwargs)
        context['problem'] = get_object_or_404(Problem, id=self.object.problem.id)
        return context

    @reversion.create_revision()
    def form_valid(self, form):
        # Don't save if the problem is locked
        if self.object.problem.locked:
            raise Http404()
        self.object = form.save(commit=False)
        self.object.author = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.object.get_absolute_url())

class IdeaRevisionView(DetailView):
    template_name = 'idea_revision.html'
    model = Idea

    def get_context_data(self, *args, **kwargs):
        context = super(IdeaRevisionView, self).get_context_data(**kwargs)
        context['revisions'] = list()
        context['problem'] = self.object.problem
        revisions = reversion.get_for_object(self.object)
        for rev in revisions:
            r = rev.object_version.object
            context['revisions'].append({
                'description': r.content,
                'author': r.author,
                'modified': r.modified
            })
        return context
