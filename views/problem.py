import re
import time
from datetime import datetime
from lib.diff import inline_diff

from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect
from django.views.generic import DetailView
from django.views.generic.edit import FormView, CreateView, UpdateView
from django.views.generic.base import RedirectView
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.utils.decorators import method_decorator
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.db.models import Q

import settings

from django_options import get_option
import reversion

from dnstorm.models import Problem, Idea, Criteria, Vote, Comment, Message
from dnstorm.forms import ProblemForm, IdeaForm, CommentForm, CriteriaForm

def problem_form_valid(obj, form):
    """
    Save the object, clear the criterias and add the submited ones in
    `request.POST`. This method will be the same for ProblemCreateView and
    ProblemUpdateView.
    """
    # Save first
    obj.object = form.save(commit=False)
    obj.object.author = obj.request.user
    obj.object.save()

    # Then fit the criterias in
    obj.object.criteria.clear()
    regex = re.compile('^criteria_([0-9]+)$')
    criteria = Criteria.objects.filter(id__in=[m.group(1) for m in [regex.match(p) for p in obj.request.POST] if m])
    for c in criteria:
        obj.object.criteria.add(c)
    obj.object.save()

    # Mailing options
    if form.cleaned_data['notice'] or form.cleaned_data['invite']:
        site_name = get_option('site_name') if get_option('site_name') else settings.DNSTORM['site_name']

    # Notice mailing
    if form.cleaned_data['notice']:
        recipients = [u.email for u in obj.object.get_message_recipients()]
        subject = _('%(site_name)s: Problem updated' % { 'site_name': site_name})
        context = {
            'site_name': site_name,
            'problem_url': reverse('problem', kwargs={'slug': obj.object.slug}),
            'problem_revision_url': reverse('problem_revision', kwargs={'pk': obj.object.id})
        }
        content = render_to_string('mail/notice.txt', context)
        if settings.DEBUG:
            print '[%s] "MAIL would be sent to %s"' % (time.strftime('%d/%b/%Y %H:%M:%S'), ', '.join(recipients))
        else:
            send_mail(subject, content, settings.EMAIL_HOST_USER, recipients)

    # Invite mailing
    if form.cleaned_data['invite']:
        recipients = form.cleaned_data['invite']
        subject = _('%(site_name)s: Invitation' % { 'site_name': site_name})
        context = {
            'user': obj.request.user.get_full_name(),
            'site_name': site_name,
            'problem_url': reverse('problem', kwargs={'slug': obj.object.slug})
        }
        content = render_to_string('mail/invite.txt', context)
        if settings.DEBUG:
            print '[%s] "MAIL would be sent to %s"' % (time.strftime('%d/%b/%Y %H:%M:%S'), recipients)
        else:
            send_mail(subject, content, settings.EMAIL_HOST_USER, recipients)

    return HttpResponseRedirect(reverse('problem', kwargs={'slug':obj.object.slug}))

class ProblemCreateView(CreateView):
    template_name = 'problem_edit.html'
    form_class = ProblemForm
    model = Problem

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProblemCreateView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(ProblemCreateView, self).get_context_data(**kwargs)
        context['title'] = _('Create new problem')
        context['criteria_form'] = CriteriaForm()
        return context

    @reversion.create_revision()
    def form_valid(self, form):
        return problem_form_valid(self, form)

class ProblemUpdateView(UpdateView):
    template_name = 'problem_edit.html'
    form_class = ProblemForm
    model = Problem

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProblemUpdateView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(ProblemUpdateView, self).get_context_data(**kwargs)
        context['title'] = _('Edit problem')
        context['criteria_form'] = CriteriaForm()
        return context

    @reversion.create_revision()
    def form_valid(self, form):
        return problem_form_valid(self, form)

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

class ProblemShortView(RedirectView):
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        problem = get_object_or_404(Problem, id=kwargs['pk'])
        return reverse('problem', kwargs={'slug':problem.slug})

class ProblemView(FormView):
    template_name = 'problem.html'
    form_class = IdeaForm

    def dispatch(self, request, *args, **kwargs):
        self.problem = get_object_or_404(Problem, slug=self.kwargs['slug'])
        return super(ProblemView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(ProblemView, self).get_context_data(**kwargs)
        context['title'] = self.problem.title
        context['problem'] = self.problem
        context['bulletin'] = Message.objects.filter(problem=self.problem).order_by('-modified')[:4]
        ideas_qs = Q(problem=self.problem)
        if self.problem.blind:
            ideas_qs |= Q(author=self.request.user)
        context['ideas'] = Idea.objects.filter(ideas_qs)
        context['idea_actions'] = True
        if not self.request.user.is_authenticated():
            return context
        if self.problem.max > 0:
            context['user_ideas_left'] = self.problem.max - Idea.objects.filter(problem=self.problem, author=self.request.user).count()
        else:
            context['user_ideas_left'] = 1
        for idea in context['ideas']:
            user_vote = Vote.objects.filter(idea=idea, author=self.request.user)
            idea.user_vote = user_vote[0] if len(user_vote) else False
            idea.comments = Comment.objects.filter(idea=idea).order_by('modified')
            idea.comment_form = CommentForm(initial={'idea': idea.id})
            if self.problem.vote_author:
                idea.votes = Vote.objects.filter(idea=idea).order_by('date')
        return context

    @reversion.create_revision()
    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.problem = self.problem
        obj.author = self.request.user
        obj.save()
        return HttpResponseRedirect(reverse('problem', kwargs={'slug':self.problem.slug}))
