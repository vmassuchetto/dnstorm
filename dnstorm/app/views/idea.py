from datetime import datetime
from lxml.html.diff import htmldiff
import bleach
import json
import re
import random
import string

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.forms.util import ErrorList
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_protect
from django.views.generic import DetailView, RedirectView
from django.views.generic.edit import CreateView, UpdateView

from dnstorm import settings
from dnstorm.app import models
from dnstorm.app import forms
from dnstorm.app import permissions
from dnstorm.app.forms import IdeaForm
from dnstorm.app.utils import get_object_or_none, activity_count, get_option, activity_register

class IdeaView(RedirectView):
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        idea = get_object_or_404(models.Idea, id=kwargs['pk'])
        return reverse('problem_idea', kwargs={'pk':idea.problem.id, 'slug': idea.problem.slug, 'idea': idea.id})

class IdeaCreateView(RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        """
        Creates a draft idea for the user to start edition.
        """
        p = get_object_or_404(models.Problem, id=kwargs['pk'])
        if not permissions.problem(obj=p, user=self.request.user, mode='contribute'):
            raise PermissionDenied
        i = models.Idea.objects.create(
            problem=p,
            published=False,
            slug=''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(100)),
            author=self.request.user)
        return reverse('idea_update', kwargs={'pk': i.id})

class IdeaUpdateView(UpdateView):
    template_name = '_update_idea.html'
    form_class = IdeaForm
    model = models.Idea

    @method_decorator(login_required)
    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        i = get_object_or_404(models.Idea, id=kwargs['pk'])
        if not permissions.idea(obj=i, user=self.request.user, mode='edit'):
            raise PermissionDenied
        self.idea = i
        return super(IdeaUpdateView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self, **kwargs):
        kwargs = super(IdeaUpdateView, self).get_form_kwargs()
        kwargs.update({'problem': self.object.problem})
        return kwargs

    def post(self, *args, **kwargs):
        """
        Checks for delete actions from forms.DeleteForm.
        """

        yes = args[0].POST.get('yes', None)

        # Delete idea

        try:
            delete_idea = int(args[0].POST.get('delete_idea', None))
        except:
            delete_idea = False
        if delete_idea:
            idea = get_object_or_404(models.Idea, id=delete_idea)
            if yes and permissions.idea(obj=idea, user=args[0].user, mode='manage'):
                i = idea
                idea.delete()
                messages.success(args[0], _('The idea was deleted.'))
                return HttpResponseRedirect(reverse('problem_tab_ideas', kwargs={'pk': i.problem.id, 'slug':i.problem.slug}))

        if not yes and delete_idea:
            messages.warning(args[0], _('You need to mark the checkbox to really delete.'))
            return HttpResponseRedirect(reverse('idea_update', kwargs={'pk': i.id}))

        return super(IdeaUpdateView, self).post(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(IdeaUpdateView, self).get_context_data(**kwargs)
        context['problem'] = self.object.problem
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['delete_form'] = forms.DeleteForm()
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Problems'), 'url': reverse('home') },
            { 'title': self.object.problem.title, 'url': self.object.problem.get_absolute_url() },
            { 'title': '%s #%d' % (_('Idea'), self.object.id), 'url': reverse('idea', kwargs={ 'pk': self.object.id }) },
            { 'title': _('Update'), 'url': reverse('idea_update', kwargs={ 'pk': self.object.id }), 'classes': 'current' } ]

    def form_valid(self, form, *args, **kwargs):
        """
        Validates the idea form for the ``IdeaUpdateView``.
        """

        super(IdeaUpdateView, self).form_valid(form, *args, **kwargs)

        self.object = form.save(commit=False)
        if not permissions.problem(user=self.request.user, obj=self.object.problem, mode='contribute'):
            raise PermissionDenied

        # Base data
        if self.request.POST.get('publish', None):
            self.object.published = True
            return_url = self.object.get_absolute_url()
        else:
            self.object.published = False
            return_url = reverse('idea_update', kwargs={'pk': self.object.id})
        self.object.save()

        criteria = dict()
        r = re.compile('^([0-9]+)__(.+)$')
        for f in form.fields:
            _r = r.match(f)
            if not _r: continue;
            if _r.group(1) not in criteria.keys():
                criteria[_r.group(1)] = {
                    'field_name': f,
                    'object': get_object_or_404(models.Criteria, id=_r.group(1)),
                }
            criteria[_r.group(1)][_r.group(2)] = form.cleaned_data[f]

        # Specific validation rules

        updated = list()
        for c in criteria:
            ic, created = models.IdeaCriteria.objects.get_or_create(
                idea=self.object, criteria=criteria[c]['object'],
                description=criteria[c]['description'])

            # Test for 'scale' format
            if 'value_scale' in criteria[c] and \
                (criteria[c]['value_scale'] < criteria[c]['object'].min or \
                criteria[c]['value_scale'] > criteria[c]['object'].max):
                form._errors[criteria[c]['field_name']] = ErrorList([
                    _('Provide a value within the specified range.')
                ])
            elif 'value_scale' in criteria[c]:
                ic.value_scale = criteria[c]['value_scale']

            # Values for all the rest
            else:
                k = 'value_%s' % ic.criteria.fmt
                setattr(ic, k, criteria[c][k])

            updated.append(ic)
            verb = 'created' if created else 'updated'

        # Something went wront
        if len(form._errors) > 0:
            return self.form_invalid(form)
        # Save everything if it's ok
        else:
            [ic.save() for ic in updated]

        # Delete remaining criteria
        models.IdeaCriteria.objects \
            .exclude(id__in=[ic.id for ic in updated]) \
            .filter(idea=self.object).delete()

        # Response
        if self.object.published == True:
            activity_register(self.request.user, self.object)
        messages.success(self.request, _('Your idea was successfully saved.'))
        return HttpResponseRedirect(return_url)
