import re
import time
from datetime import datetime

from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect
from django.views.generic import DetailView
from django.views.generic.edit import FormView, CreateView, UpdateView
from django.views.generic.base import TemplateView, RedirectView
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.utils.decorators import method_decorator
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.db.models import Q
from django.db.models.query import EmptyQuerySet

import settings

from django_options import get_option
import reversion
import diff_match_patch as _dmp
from dnstorm.lib.diff import diff_prettyHtml

from dnstorm.models import Problem, Invite, Idea, Criteria, Vote, Comment, Message, ActivityManager
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

        # Save invites to give permissions for these users when they login
        recipients = form.cleaned_data['invite']
        for r in recipients.split(','):
            Invite(problem=obj.object, email=r).save()

        # Send the e-mails
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
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['title'] = _('Create new problem')
        context['criteria_form'] = CriteriaForm()
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Problems'), 'url': reverse('home') },
            { 'title': _('Create new problem'), 'url': reverse('problem_new'), 'classes': 'current' } ]

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
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['title'] = _('Edit problem')
        context['criteria_form'] = CriteriaForm()
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Problems'), 'url': reverse('home') },
            { 'title': self.object.title, 'url': self.object.get_absolute_url() },
            { 'title': _('Update'), 'url': reverse('problem_edit', kwargs={'slug':self.object.slug}), 'classes': 'current' } ]

    @reversion.create_revision()
    def form_valid(self, form):
        return problem_form_valid(self, form)

class ProblemRevisionView(DetailView):
    template_name = 'problem_revision.html'
    model = Problem

    def get_context_data(self, *args, **kwargs):
        context = super(ProblemRevisionView, self).get_context_data(**kwargs)
        context['breadcrumbs'] = self.get_breadcrumbs()

        dmp = _dmp.diff_match_patch()

        checkboxes = ('blind', 'locked', 'max', 'open', 'public', 'voting', 'vote_count', 'vote_author')
        true_messages = {
            'blind': _('The problem was set to blind contribution mode.'),
            'locked': _('The problem was locked for contributions.'),
            'max': _('Max ideas per user set to %d.'),
            'open': _('Contributions opened for any logged user.'),
            'public': _('Problem set to be publicly available.'),
            'voting': _('Ideas votation were opened.'),
            'vote_count': _('Vote counts will be displayed.'),
            'vote_author': _('Vote authors will be displayed.')
        }
        false_messages = {
            'blind': _('No longer in blind contribution mode.'),
            'locked': _('Problem unlocked for contributions.'),
            'max': _('Untilimed ideas per user.'),
            'open': _('Only participants will be able to contribute.'),
            'public': _('The problem is no longer public.'),
            'voting': _('Ideas votation were closed.'),
            'vote_count': _('Vote counts will no longer be displayed.'),
            'vote_author': _('Vote authors will no longer be displayed.')
        }

        revisions = list()
        versions = reversion.get_for_object(self.object)
        for i in range(0, len(versions) - 1):
            new = versions[i].object_version.object
            old = versions[i+1].object_version.object
            detail = ''

            if new.title != old.title or new.description != old.description:
                diff = dmp.diff_main('<h3>' + old.title + '</h3>' + old.description, '<h3>' + new.title + '</h3>' + new.description)
                dmp.diff_cleanupSemantic(diff)
                detail += diff_prettyHtml(diff)

            checkboxes_detail = ''
            for c in checkboxes:
                if getattr(new, c) != getattr(old, c):
                    checkboxes_detail += '<li>%s%s%s</li>' % (
                        '<ins>' if c else '<del>',
                        true_messages[c] if c else false_messages[c],
                        '</ins>' if c else '</del>')

            if checkboxes_detail:
                detail += '<h5>' + _('Advanced options') + '</h5><ul>%s</ul>' % checkboxes_detail

            revisions.append({
                'id': versions[i].id,
                'detail': detail,
                'author': versions[i].revision.user,
                'modified': versions[i].object_version
            })

        first = versions[len(versions)-1]
        detail = '<h3>' + first.object_version.object.title + '</h3>' + first.object_version.object.description
        for c in first.object_version.object.criteria.all():
            detail += '<a class="button-criteria" data-tooltip title="%s">%s</a>&nbsp;' % (c.description, c.name)

        revisions.append({
            'id': first.id,
            'detail': detail,
            'author': first.revision.user,
            'modified': first.object_version
        })
        context['revisions'] = revisions
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Problems'), 'url': reverse('home') },
            { 'title': self.object.title, 'url': self.object.get_absolute_url() },
            { 'title': _('Revisions'), 'url': reverse('problem_revision', kwargs={'slug':self.object.slug}), 'classes': 'current' } ]

class ProblemRevisionItemView(RedirectView):
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        revision = get_object_or_404(reversion.models.Version, id=kwargs['pk'])
        return reverse('problem_revision', kwargs={'id':revision.object.id}) + '#revision-' + str(revision.id)

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
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['activities'] = ActivityManager().get(limit=4)
        context['title'] = self.problem.title
        context['problem'] = self.problem
        context['comments'] = Comment.objects.filter(problem=self.problem)
        context['bulletin'] = Message.objects.filter(problem=self.problem).order_by('-modified')[:4]
        context['problem_comment_form'] = CommentForm(initial={'problem': self.problem.id})

        # Ideas

        ideas_qs = Q(problem=self.problem)
        if not self.request.user.is_authenticated():
            ideas_qs = False
        elif self.problem.blind:
            ideas_qs &= Q(author=self.request.user)
        if ideas_qs:
            context['ideas'] = Idea.objects.filter(ideas_qs)
        else:
            context['ideas'] = Idea.objects.none()
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

    def get_breadcrumbs(self):
        return [
            { 'title': _('Problems'), 'url': reverse('home') },
            { 'title': self.problem.title, 'url': self.problem.get_absolute_url(), 'classes': 'current' } ]

    @reversion.create_revision()
    def form_valid(self, form):
        """
        That' actually an Idea object creation procedure, since the form in
        this view is meant to show problem information but to save Idea
        information.
        """
        obj = form.save(commit=False)
        obj.problem = self.problem
        obj.author = self.request.user
        obj.save()
        return HttpResponseRedirect(obj.get_absolute_url())

class ProblemSearchView(TemplateView):
    pass
