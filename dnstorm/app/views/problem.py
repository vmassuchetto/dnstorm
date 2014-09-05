import re
import time
from datetime import datetime

from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseRedirect
from django.views.generic import DetailView
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView
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

import bleach
import reversion
import diff_match_patch as _dmp
from notification import models as notification

from dnstorm import settings
from dnstorm.app import permissions
from dnstorm.app.lib.diff import diff_prettyHtml
from dnstorm.app.lib.get import get_object_or_none
from dnstorm.app import models
from dnstorm.app import forms
from dnstorm.app.views.idea import idea_save

def problem_save(obj, form):
    """
    Save the object, clear the criterias and add the submited ones in
    ``request.POST``. This method will be the same for ProblemCreateView and
    ProblemUpdateView.
    """

    # Save first

    obj.object = form.save(commit=False)
    obj.object.author = obj.request.user
    obj.object.description = bleach.clean(obj.object.description,
        tags=settings.SANITIZER_ALLOWED_TAGS,
        attributes=settings.SANITIZER_ALLOWED_ATTRIBUTES,
        styles=settings.SANITIZER_ALLOWED_STYLES,
        strip=True, strip_comments=True)
    obj.object.save()

    # Criterias

    obj.object.criteria.through.objects.all().delete()
    criterias = [i for i in obj.request.POST.get('criteria', '').split('|') if i.isdigit()]
    for c in models.Criteria.objects.filter(id__in=criterias):
        obj.object.criteria.add(c)

    # Invitations

    from_user = obj.object.author.get_full_name()
    emails = [u.email for u in obj.object.contributor.all()]
    to_add = list()

    for email in sorted(set(obj.request.POST.getlist('invitation', []))):

        # User already invited
        if models.Invitation.objects.filter(problem=obj.object.id, email=email).exists():
            continue

        # User is already a contributor
        if email in emails:
            continue

        # Save user to add as contributor if exists
        user = get_object_or_none(User, email=email)
        if user:
            to_add.append(user)
            continue

        models.Invitation(problem=obj.object, email=email).save()
        fake_user = User(id=1, username=i, email=email)
        notification.send([fake_user], 'invitation', { 'from_user': from_user, 'problem': obj.object })

    # Contributors

    new_contributors = User.objects.filter(id__in=[i for i in obj.request.POST.get('contributor', '').split('|') if i.isdigit()])
    if not new_contributors:
        obj.object.contributor.through.objects.all().delete()
    current_contributors = obj.object.contributor.all()

    c = [c.id for c in list(set(current_contributors) - set(new_contributors))]
    obj.object.contributor.through.objects.filter(id__in=c).delete()

    c = list(set(new_contributors) - set(current_contributors))
    for u in c:
        obj.object.contributor.add(u)
        notification.send([u], 'contributor', { 'from_user': from_user, 'problem': obj.object })

    for user in to_add:
        obj.object.contributor.add(user)

    obj.object.save()

    # Success

    messages.success(obj.request, _('Problem saved'))
    return HttpResponseRedirect(reverse('problem', kwargs={'slug':obj.object.slug}))

class ProblemCreateView(CreateView):
    template_name = 'problem_edit.html'
    form_class = forms.ProblemForm
    model = models.Problem

    @method_decorator(login_required)
    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        return super(ProblemCreateView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(ProblemCreateView, self).get_context_data(**kwargs)
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['title'] = _('Create new problem')
        context['criteria_form'] = forms.CriteriaForm()
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Problems'), 'url': reverse('home') },
            { 'title': _('Create new problem'), 'url': reverse('problem_new'), 'classes': 'current' } ]

    @reversion.create_revision()
    def form_valid(self, form):
        return problem_save(self, form)

class ProblemUpdateView(UpdateView):
    template_name = 'problem_edit.html'
    form_class = forms.ProblemForm
    model = models.Problem

    @method_decorator(login_required)
    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        obj = get_object_or_404(models.Problem, slug=kwargs['slug'])
        if not permissions.problem(obj=obj, user=self.request.user, mode='manage'):
            raise PermissionDenied
        return super(ProblemUpdateView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(ProblemUpdateView, self).get_context_data(**kwargs)
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['title'] = _('Edit problem')
        context['criteria_form'] = forms.CriteriaForm()
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Problems'), 'url': reverse('home') },
            { 'title': self.object.title, 'url': self.object.get_absolute_url() },
            { 'title': _('Update'), 'url': reverse('problem_edit', kwargs={'slug':self.object.slug}), 'classes': 'current' } ]

    @reversion.create_revision()
    def form_valid(self, form):
        return problem_save(self, form)

class ProblemDeleteView(DeleteView):
    template_name = 'problem_confirm_delete.html'
    model = models.Problem
    success_url = '/'

    def dispatch(self, *args, **kwargs):
        obj = get_object_or_404(Problem, slug=kwargs['slug'])
        if not permissions.problem(obj=obj, user=self.request.user, mode='contribute'):
            raise PermissionDenied
        if len(self.request.POST) > 0:
            messages.success(self.request, _('Problem deleted'))
        return super(ProblemDeleteView, self).dispatch(*args, **kwargs)

class ProblemRevisionView(DetailView):
    template_name = 'problem_revision.html'
    model = models.Problem

    def dispatch(self, *args, **kwargs):
        obj = get_object_or_404(Problem, slug=kwargs['slug'])
        if not permissions.problem(obj=obj, user=self.request.user, mode='contribute'):
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
        if not permissions.problem(obj=obj, user=self.request.user, mode='contribute'):
            raise PermissionDenied
        return super(ProblemRevisionItemView, self).dispatch(*args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        revision = get_object_or_404(reversion.models.Version, id=kwargs['pk'])
        return reverse('problem_revision', kwargs={'id':revision.object.id}) + '#revision-' + str(revision.id)

class ProblemView(FormView):
    template_name = 'problem.html'
    form_class = forms.IdeaForm

    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        self.problem = get_object_or_404(models.Problem, slug=self.kwargs['slug'])
        if not permissions.problem(obj=self.problem, user=self.request.user, mode='contribute'):
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
        context['title'] = self.problem.title
        context['sidebar'] = True
        context['problem'] = self.problem
        context['problem_perm_manage'] = permissions.problem(obj=self.problem, user=user, mode='manage')
        context['problem_perm_contribute'] = permissions.problem(obj=self.problem, user=user, mode='contribute')
        context['comments'] = models.Comment.objects.filter(problem=self.problem)
        context['comment_form'] = forms.CommentForm()
        context['criterias'] = models.Criteria.objects.filter(problem=self.problem)
        context['all_ideas'] = models.Idea.objects.filter(problem=self.problem)

        # Alternatives

        context['alternatives'] = list()
        for a in models.Alternative.objects.filter(problem=self.problem):
            a.fill_data(self.request.user)
            context['alternatives'].append(a)

        # Ideas

        ideas_qs = Q(problem=self.problem) & permissions.idea_queryset(user=user)
        if ideas_qs:
            context['ideas'] = models.Idea.objects.filter(ideas_qs)
        else:
            context['ideas'] = models.Idea.objects.none()
        context['idea_actions'] = True

        # Voting and comments

        for idea in context['ideas']:
            idea.fill_data(user=self.request.user)

        for comment in context['comments']:
            comment.perms_edit = permissions.comment(obj=comment, user=self.request.user, mode='manage')

        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Problems'), 'url': reverse('home') },
            { 'title': self.problem.title, 'url': self.problem.get_absolute_url(), 'classes': 'current' } ]

    @reversion.create_revision()
    def form_valid(self, form):
        return idea_save(self, form)
