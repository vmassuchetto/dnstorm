from django.views.generic import TemplateView
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator

from dnstorm.app.models import Problem, Criteria, ActivityManager

class CriteriaListView(TemplateView):
    template_name = 'criteria.html'
    model = Criteria

    def get_context_data(self, *args, **kwargs):
        context = super(CriteriaListView, self).get_context_data(**kwargs)
        context['breadcrumbs'] = self.get_breadcrumbs()
        criterias = Paginator(Criteria.objects.all().order_by('name'), 25)
        page = self.request.GET['page'] if 'page' in self.request.GET else 1
        context['criterias'] = criterias.page(page)
        return context

    def get_breadcrumbs(self):
        return [ { 'title': _('Criterias'), 'classes': 'current' } ]

class CriteriaProblemView(TemplateView):
    template_name = 'home.html'

    def dispatch(self, request, *args, **kwargs):
        self.criteria = get_object_or_404(Criteria, slug=kwargs['slug'])
        return super(CriteriaProblemView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(CriteriaProblemView, self).get_context_data(**kwargs)
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['criteria'] = self.criteria
        problems = Paginator(Problem.objects.filter(criteria=self.criteria).order_by('-modified'), 25)
        page = self.request.GET['page'] if 'page' in self.request.GET else 1
        context['problems'] = problems.page(page)
        activities = ActivityManager()
        context['activities'] = activities.get(limit=4)
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Problems'), 'url': reverse('home') },
            { 'title': _('Criterias'), 'url': reverse('criteria_list') },
            { 'title': self.criteria.name, 'url': self.criteria.get_absolute_url(), 'classes': 'current' } ]

