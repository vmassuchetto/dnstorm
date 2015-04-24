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
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from dnstorm import settings
from dnstorm.app import models
from dnstorm.app import forms
from dnstorm.app import permissions
from dnstorm.app.forms import AlternativeForm
from dnstorm.app.utils import get_object_or_none, activity_count, get_option, activity_register
from dnstorm.app.views.problem import problem_buttons

class AlternativeView(RedirectView):
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        idea = get_object_or_404(models.AlternativeView, id=kwargs['pk'])
        return reverse('problem_alternative', kwargs={'pk':alternative.problem.id, 'slug': alternative.problem.slug, 'idea': alternative.id})

class AlternativeCreateView(RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        """
        Creates a draft alternative for the user to start edition.
        """
        # Validation
        p = get_object_or_404(models.Problem, id=kwargs['problem'])
        if not permissions.problem(obj=p, user=self.request.user, mode='contribute'):
            raise PermissionDenied
        if p.criteria_set.all().count() == 0:
            raise PermissionDenied

        # Commit
        a = models.Alternative.objects.create(
            problem=p,
            published=False,
            author=self.request.user)
        return reverse('alternative_update', kwargs={'pk': a.id})

class AlternativeUpdateView(UpdateView):
    template_name = '_update_alternative.html'
    form_class = AlternativeForm
    model = models.Alternative

    @method_decorator(login_required)
    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        a = get_object_or_404(models.Alternative, id=kwargs['pk'])
        if not permissions.alternative(obj=a, user=self.request.user, mode='manage'):
            raise PermissionDenied
        self.alternative = a
        return super(AlternativeUpdateView, self).dispatch(request, *args, **kwargs)

    def post(self, *args, **kwargs):
        """
        Checks for delete actions from forms.DeleteForm.
        """
        yes = args[0].POST.get('yes', None)

        # Delete alternative

        try:
            delete_alternative = int(args[0].POST.get('delete_alternative', None))
        except:
            delete_alternative = False
        if delete_alternative:
            alternative = get_object_or_404(models.Alternative, id=delete_alternative)
            if yes and permissions.idea(obj=idea, user=args[0].user, mode='manage'):
                a= alternative
                alternative.delete()
                messages.success(args[0], _('The alternative was deleted.'))
                return HttpResponseRedirect(reverse('problem_tab_alternatives', kwargs={'pk': a.problem.id, 'slug':a.problem.slug}))

        if not yes and delete_alternative:
            messages.warning(args[0], _('You need to mark the checkbox to really delete.'))
            return HttpResponseRedirect(reverse('alternative_update', kwargs={'pk': a.id}))

        return super(AlternativeUpdateView, self).post(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(AlternativeUpdateView, self).get_context_data(**kwargs)
        context['problem'] = self.object.problem
        context['info'] = self.get_info()
        context['delete_form'] = forms.DeleteForm()
        return context

    def get_info(self):
        return {
            'icon': 'lightbulb',
            'icon_url': reverse('problem', kwargs={'pk': self.object.problem.id, 'slug': self.object.problem.slug}),
            'title': _('Post idea to problem: %s' % self.object.problem.title),
            'title_url': self.object.problem.get_absolute_url(),
            'buttons': problem_buttons(self.request, self.object.problem),
            'show': permissions.problem(obj=self.object, user=self.request.user, mode='manage')
        }

    def form_valid(self, form, *args, **kwargs):
        """
        Validates the idea form for the ``IdeaUpdateView``.
        """

        super(AlternativeUpdateView, self).form_valid(form, *args, **kwargs)

        self.object = form.save(commit=False)
        if not permissions.problem(user=self.request.user, obj=self.object.problem, mode='contribute'):
            raise PermissionDenied

        # Base data
        if self.request.POST.get('publish', None):
            self.object.published = True
            return_url = self.object.get_absolute_url()
        else:
            self.object.published = False
            return_url = reverse('alternative_update', kwargs={'pk': self.object.id})
        self.object.save()

        exit(1)

        # Response
        if self.object.published == True:
            activity_register(self.request.user, self.object)
        messages.success(self.request, _('The alternative was successfully saved.'))
        return HttpResponseRedirect(return_url)

class AlternativeDeleteView(DeleteView):
    model = models.Alternative

    @method_decorator(login_required)
    def get_object(self, *args, **kwargs):
        alternative = get_object_or_404(models.Alternative, id=kwargs['pk'])
        if not permissions.alternative(obj=alternative, user=self.request.user, mode='manage'):
            raise PermissionDenied
        return idea
