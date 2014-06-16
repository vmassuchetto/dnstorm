import re
import json
from datetime import datetime

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from django.views.generic import DetailView, RedirectView
from django.views.generic.edit import UpdateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.contrib import messages

from dnstorm.app import models
from dnstorm.app.forms import IdeaForm
from dnstorm.app import permissions

import reversion
import diff_match_patch as _dmp
from dnstorm.app.lib.diff import diff_prettyHtml

def idea_form_valid(obj, form):
    """
    Validates the idea form for the ``IdeaUpdateView``.
    """

    # Save idea

    object = form.save(commit=False)
    object.problem = obj.problem if hasattr(obj, 'problem') else object.problem
    object.author = obj.request.user
    object.save()

    # Criterias ratings

    models.IdeaCriteria.objects.filter(idea=object).delete()
    for c in object.problem.criteria.all():
        models.IdeaCriteria(
            idea=models.Idea.objects.get(id=object.id),
            criteria=models.Criteria.objects.get(id=c.id),
            stars=form.cleaned_data['criteria_%d' % c.id]).save()

    # Problem activity update

    object.problem.last_activity = datetime.now()
    object.problem.save()

    messages.success(obj.request, _('Idea saved.'))
    return HttpResponseRedirect(object.get_absolute_url())

class IdeaView(RedirectView):
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        idea = get_object_or_404(Idea, id=kwargs['pk'])
        return reverse('idea', kwargs={'slug':idea.problem.slug, 'pk': idea.id})

class IdeaUpdateView(UpdateView):
    template_name = 'idea_edit.html'
    form_class = IdeaForm
    model = models.Idea

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        obj = get_object_or_404(models.Idea, id=kwargs['pk'])
        if not permissions.idea(obj=obj, user=self.request.user, mode='edit'):
            raise PermissionDenied
        return super(IdeaUpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(IdeaUpdateView, self).get_context_data(**kwargs)
        context['problem'] = get_object_or_404(models.Problem, id=self.object.problem.id)
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['activities'] = models.ActivityManager().get_objects(limit=4)
        return context

    @reversion.create_revision()
    def form_valid(self, form):
        return idea_form_valid(self, form)

    def get_breadcrumbs(self):
        return [
            { 'title': _('Problems'), 'url': reverse('home') },
            { 'title': self.object.problem.title, 'url': self.object.problem.get_absolute_url() },
            { 'title': '%s #%d' % (_('Idea'), self.object.id), 'url': reverse('idea', kwargs={ 'slug': self.object.problem.slug, 'pk': self.object.id }) },
            { 'title': _('Update'), 'url': reverse('idea_edit', kwargs={ 'slug':self.object.problem.slug, 'pk': self.object.id }), 'classes': 'current' } ]

class IdeaRevisionView(DetailView):
    template_name = 'idea_revision.html'
    model = models.Idea

    def get_context_data(self, *args, **kwargs):
        context = super(IdeaRevisionView, self).get_context_data(**kwargs)
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['problem'] = self.object.problem
        context['activities'] = models.ActivityManager().get_objects(limit=4)
        context['revisions'] = list()

        dmp = _dmp.diff_match_patch()
        versions = reversion.get_for_object(self.object)
        for i in range(0, len(versions) - 1):
            new = versions[i].object_version.object
            old = versions[i+1].object_version.object
            detail = ''

            if new.title != old.title or new.content != old.content:
                diff = dmp.diff_main('<h3>' + old.title + '</h3>' + old.content, '<h3>' + new.title + '</h3>' + new.content)
                dmp.diff_cleanupSemantic(diff)
                detail = diff_prettyHtml(diff)

            context['revisions'].append({
                'id': versions[i].id,
                'detail': detail,
                'author': versions[i].object_version.object.author,
                'updated': versions[i].object_version.object.updated,
            })

        first = versions[len(versions)-1]
        detail = '<h3>' + first.object_version.object.title + '</h3>' + first.object_version.object.content
        context['revisions'].append({
            'id': first.id,
            'detail': detail,
            'author': first.object_version.object.author,
            'updated': first.object_version.object.updated,
        })

        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Problems'), 'url': reverse('home') },
            { 'title': self.object.problem.title, 'url': self.object.problem.get_absolute_url() },
            { 'title': '%s #%d' % (_('Idea'), self.object.id), 'url': reverse('idea', kwargs={ 'slug': self.object.problem.slug, 'pk': self.object.id }) },
            { 'title': _('Revisions'), 'url': reverse('idea_revision', kwargs={'slug':self.object.problem.slug, 'pk': self.object.id}), 'classes': 'current' } ]
