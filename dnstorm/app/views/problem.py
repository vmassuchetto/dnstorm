import re
import time
from datetime import datetime

from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseRedirect
from django.views.generic import DetailView
from django.views.generic.edit import FormView, CreateView, UpdateView
from django.views.generic.base import TemplateView, RedirectView
from django.contrib.auth import get_user
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.db.models import Q
from django.db.models.query import EmptyQuerySet
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

import reversion
import diff_match_patch as _dmp

from dnstorm import settings
from dnstorm.app import permissions
from dnstorm.app.lib.diff import diff_prettyHtml
from dnstorm.app.models import Problem, Invite, Idea, \
    Criteria, Vote, Comment, Alternative, \
    Message, ActivityManager, Quantifier
from dnstorm.app.forms import ProblemForm, IdeaForm, \
    CommentForm, CriteriaForm, AlternativeForm
from dnstorm.app.views.idea import idea_form_valid

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

    # Managers and contributors

    for i in obj.request.POST.get('contributor', '').split('|'):
        try:
            obj.object.contributor.add(int(i))
        except ValueError:
            continue

    for i in obj.request.POST.get('manager', '').split('|'):
        try:
            obj.object.manager.add(int(i))
        except ValueError:
            continue

    obj.object.save()

    # Criterias

    obj.object.criteria.clear()
    regex_criteria = re.compile('^criteria_([0-9]+)$')
    criteria = Criteria.objects.filter(id__in=[m.group(1) for m in [regex_criteria.match(p) for p in obj.request.POST] if m])
    for c in criteria:
        obj.object.criteria.add(c)
    obj.object.save()

    # New quantifiers

    new_ids = list()
    new = dict() # new[<temporary id>] = [<format>, <name>, <help text>]
    regex_new_name = re.compile('^quantifiername_new([0-9]+)_(boolean|number|text|daterange)$')
    regex_new_help = re.compile('^quantifierhelp_new([0-9]+)_(boolean|number|text|daterange)$')

    for m in [m for m in [regex_new_name.match(p) for p in obj.request.POST] if m]:
        new.setdefault(m.group(1), dict())
        new[m.group(1)]['format'] = m.group(2)
        new[m.group(1)]['name'] = obj.request.POST[m.group(0)]
    for m in [m for m in [regex_new_help.match(p) for p in obj.request.POST] if m]:
        new[m.group(1)]['help'] = obj.request.POST[m.group(0)]  # Help text
    for q in new.values():
        try:
            n = Quantifier(problem=obj.object, format=q['format'], name=q['name'], help=q['help'])
            n.save()
            new_ids.append(n.id)
        except:
            messages.warning(obj.request, _('There was an error saving the quantifier \'%s\'.' % q['name']))
            continue

    # Update quantifiers

    update = dict() # update[<id>] = [<format>, <name>, <help text>]
    regex_name = re.compile('^quantifiername_([0-9]+)_(boolean|number|text|daterange)$')
    regex_help = re.compile('^quantifierhelp_([0-9]+)_(boolean|number|text|daterange)$')
    for m in [m for m in [regex_name.match(p) for p in obj.request.POST] if m]:
        update.setdefault(m.group(1), dict())
        update[m.group(1)]['id'] = m.group(1)
        update[m.group(1)]['format'] = m.group(2)
        update[m.group(1)]['name'] = obj.request.POST[m.group(0)]
    for m in [m for m in [regex_help.match(p) for p in obj.request.POST] if m]:
        update[m.group(1)]['help'] = obj.request.POST[m.group(0)]
    for q in update.values():
        try:
            Quantifier(id=q['id'], problem=obj.object, format=q['format'], name=q['name'], help=q['help']).save()
        except:
            messages.warning(obj.request, _('There was an error saving the quantifier \'%s\'.' % q['name']))
            continue

    # Remove remaining quantifiers

    ids_to_keeep = new_ids + [ int(k) for k in update.keys() ]
    Quantifier.objects.filter(problem=obj.object.id).exclude(pk__in=ids_to_keeep).delete()

    # Success

    messages.success(obj.request, _('Problem saved'))
    return HttpResponseRedirect(reverse('problem', kwargs={'slug':obj.object.slug}))

class ProblemCreateView(CreateView):
    template_name = 'problem_edit.html'
    form_class = ProblemForm
    model = Problem

    @method_decorator(login_required)
    @method_decorator(csrf_protect)
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
    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        obj = get_object_or_404(Problem, slug=kwargs['slug'])
        if not permissions.problem(obj=obj, user=self.request.user, mode='edit'):
            raise PermissionDenied
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

    def dispatch(self, *args, **kwargs):
        obj = get_object_or_404(Problem, slug=kwargs['slug'])
        if not permissions.problem(obj=obj, user=self.request.user, mode='view'):
            raise PermissionDenied
        return super(ProblemRevisionView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(ProblemRevisionView, self).get_context_data(**kwargs)
        context['breadcrumbs'] = self.get_breadcrumbs()

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

        dmp = _dmp.diff_match_patch()
        revisions = list()
        versions = reversion.get_for_object(self.object)
        for i in range(0, len(versions) - 1):
            new = versions[i].object_version.object
            old = versions[i+1].object_version.object
            detail = ''

            # Description diff

            if new.title != old.title or new.description != old.description:
                diff = dmp.diff_main('<h3>' + old.title + '</h3>' + old.description, '<h3>' + new.title + '</h3>' + new.description)
                dmp.diff_cleanupSemantic(diff)
                detail += diff_prettyHtml(diff)

            # Criterias

            new_criterias = [v for v in versions[i].revision.version_set.all() \
                if v.content_type == ContentType.objects.get_for_model(Criteria)]
            old_criterias = [v for v in versions[i+1].revision.version_set.all() \
                if v.content_type == ContentType.objects.get_for_model(Criteria)]

            criteria = [c.object_version.object for c in old_criterias] \
                if [c.id for c in new_criterias] != [c.id for c in old_criterias] \
                else None

            # Advanced options

            checkboxes_detail = ''
            for c in checkboxes:
                if getattr(new, c) != getattr(old, c):
                    checkboxes_detail += '<li>%s%s%s</li>' % (
                        '<ins>' if getattr(new, c) else '<del>',
                        true_messages[c] if getattr(new, c) else false_messages[c],
                        '</ins>' if getattr(new, c) else '</del>')

            if checkboxes_detail:
                detail += '<h5>' + _('Advanced options') + '</h5><ul>%s</ul>' % checkboxes_detail

            revisions.append({
                'id': versions[i].id,
                'detail': detail,
                'author': versions[i].object_version.object.author,
                'updated': versions[i].object_version.object.updated,
                'criteria': criteria
            })


        first = versions[len(versions)-1]
        detail = '<h3>' + first.object_version.object.title + '</h3>' + first.object_version.object.description

        revisions.append({
            'id': first.id,
            'detail': detail,
            'author': first.object_version.object.author,
            'updated': first.object_version.object.updated,
            'criteria': first.object_version.object.criteria.all()
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

    def dispatch(self, *args, **kwargs):
        obj = get_object_or_404(Problem, slug=kwargs['slug'])
        if not permissions.problem(obj=obj, user=self.request.user, mode='view'):
            raise PermissionDenied
        return super(ProblemRevisionItemView, self).dispatch(*args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        revision = get_object_or_404(reversion.models.Version, id=kwargs['pk'])
        return reverse('problem_revision', kwargs={'id':revision.object.id}) + '#revision-' + str(revision.id)

class ProblemShortView(RedirectView):
    permanent = True

    def dispatch(self, *args, **kwargs):
        obj = get_object_or_404(Problem, slug=kwargs['slug'])
        if not permissions.problem(obj=obj, user=self.request.user, mode='view'):
            raise PermissionDenied
        return super(ProblemShortView, self).dispatch(*args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        problem = get_object_or_404(Problem, id=kwargs['pk'])
        return reverse('problem', kwargs={'slug':problem.slug})

class ProblemView(FormView):
    template_name = 'problem.html'
    form_class = IdeaForm

    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        self.problem = get_object_or_404(Problem, slug=self.kwargs['slug'])
        if not permissions.problem(obj=self.problem, user=self.request.user, mode='view'):
            raise PermissionDenied
        return super(ProblemView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(ProblemView, self).get_form_kwargs()
        kwargs['problem'] = self.problem
        return kwargs

    def get_context_data(self, *args, **kwargs):
        context = super(ProblemView, self).get_context_data(**kwargs)
        user = get_user(self.request)
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['activities'] = ActivityManager().get_objects(limit=4)
        context['title'] = self.problem.title
        context['problem'] = self.problem
        context['problem_perm_manage'] = permissions.problem(obj=self.problem, user=user, mode='manage')
        context['problem_perm_contribute'] = permissions.problem(obj=self.problem, user=user, mode='contribute')
        context['problem_short_url'] = self.request.build_absolute_uri(reverse('problem_short', kwargs={'pk': self.problem.id}))
        context['comments'] = Comment.objects.filter(problem=self.problem)
        context['bulletin'] = Message.objects.filter(problem=self.problem).order_by('-created')[:4]
        context['problem_comment_form'] = CommentForm(initial={'problem': self.problem.id})
        context['criterias'] = Criteria.objects.filter(problem=self.problem).order_by('order')
        context['alternatives'] = Alternative.objects.filter(problem=self.problem).order_by('order')
        context['alternative_form'] = AlternativeForm(initial={'problem': self.problem.id})
        context['all_ideas'] = Idea.objects.filter(problem=self.problem)

        # Ideas

        ideas_qs = Q(problem=self.problem) & permissions.idea_queryset(user=user)
        if self.problem.blind:
            ideas_qs &= Q(author=user.id)
        if ideas_qs:
            context['ideas'] = Idea.objects.filter(ideas_qs)
        else:
            context['ideas'] = Idea.objects.none()
        context['idea_actions'] = True

        # Voting and comments

        if self.problem.max > 0:
            context['user_ideas_left'] = self.problem.max - Idea.objects.filter(problem=self.problem, author=self.request.user).count()
        elif self.request.user.is_authenticated():
            context['user_ideas_left'] = 1

        for alternative in context['alternatives']:
            alternative.vote_count = Vote.objects.filter(alternative=alternative).count()
            alternative.user_vote = Vote.objects.filter(alternative=alternative, author=user.id).count()

        for idea in context['ideas']:
            user_vote = Vote.objects.filter(idea=idea, author=user.id)
            idea.user_vote = user_vote[0] if len(user_vote) else False
            idea.perms_edit = permissions.idea(obj=idea, user=self.request.user, mode='edit')
            idea.comments = Comment.objects.filter(idea=idea).order_by('created')
            idea.comment_form = CommentForm(initial={'idea': idea.id})
            if self.problem.vote_author:
                idea.votes = Vote.objects.filter(idea=idea).order_by('date')
            for comment in idea.comments:
                comment.perms_edit = permissions.comment(obj=comment, user=self.request.user, mode='edit')

        for comment in context['comments']:
            comment.perms_edit = permissions.comment(obj=comment, user=self.request.user, mode='edit')

        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Problems'), 'url': reverse('home') },
            { 'title': self.problem.title, 'url': self.problem.get_absolute_url(), 'classes': 'current' } ]

    @reversion.create_revision()
    def form_valid(self, form):
        return idea_form_valid(self, form)
