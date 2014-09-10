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

from actstream import action
from actstream.models import followers

from dnstorm import settings
from dnstorm.app import models
from dnstorm.app.forms import IdeaForm
from dnstorm.app import permissions
from dnstorm.app.lib.diff import diff_prettyHtml

import bleach
import diff_match_patch as _dmp


def idea_save(obj, form, return_format=None):
    """
    Validates the idea form for the ``IdeaUpdateView``.
    """

    # Save idea

    object = form.save(commit=False)
    object.problem = obj.problem if hasattr(obj, 'problem') else object.problem
    object.author = obj.request.user
    object.content = bleach.clean(object.content,
        tags=settings.SANITIZER_ALLOWED_TAGS,
        attributes=settings.SANITIZER_ALLOWED_ATTRIBUTES,
        styles=settings.SANITIZER_ALLOWED_STYLES,
        strip=True, strip_comments=True)

    # Remember if new

    new = False if hasattr(object, 'id') and isinstance(object.id, int) else True

    object.save()

    # Criterias ratings

    models.IdeaCriteria.objects.filter(idea=object).delete()
    for c in object.problem.criteria.all():
        models.IdeaCriteria(
            idea=models.Idea.objects.get(id=object.id),
            criteria=models.Criteria.objects.get(id=c.id),
            stars=form.cleaned_data['criteria_%d' % c.id]).save()

    # Send and action and follow the problem

    verb = 'created' if new else 'edited'
    action.send(object.author, verb=verb, action_object=object, target=object.problem)
    follow(object.author, object.problem) if object.author not in followers(object.problem) else None

    if return_format == 'obj':
        return object

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
        if not permissions.idea(obj=obj, user=self.request.user, mode='manage'):
            raise PermissionDenied
        return super(IdeaUpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(IdeaUpdateView, self).get_context_data(**kwargs)
        context['problem'] = get_object_or_404(models.Problem, id=self.object.problem.id)
        context['breadcrumbs'] = self.get_breadcrumbs()
        return context

    def form_valid(self, form):
        return idea_save(self, form)

    def get_breadcrumbs(self):
        return [
            { 'title': _('Problems'), 'url': reverse('home') },
            { 'title': self.object.problem.title, 'url': self.object.problem.get_absolute_url() },
            { 'title': '%s #%d' % (_('Idea'), self.object.id), 'url': reverse('idea', kwargs={ 'slug': self.object.problem.slug, 'pk': self.object.id }) },
            { 'title': _('Update'), 'url': reverse('idea_edit', kwargs={ 'slug':self.object.problem.slug, 'pk': self.object.id }), 'classes': 'current' } ]
