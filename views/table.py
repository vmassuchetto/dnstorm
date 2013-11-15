from django.shortcuts import get_object_or_404
from django.views.generic.base import TemplateView

from dnstorm.models import Problem, Idea, Criteria, Alternative, AlternativeItem
from dnstorm.forms import AlternativeForm

from django.utils.translation import ugettext_lazy as _

class TableView(TemplateView):
    template_name = 'table.html'

    def dispatch(self, *args, **kwargs):
        self.problem = get_object_or_404(Problem, id=self.kwargs['problem_id'])
        return super(TableView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(TableView, self).get_context_data(**kwargs)
        context['problem'] = self.problem
        context['ideas'] = Idea.objects.filter(problem=self.problem)
        context['ideas_modal'] = True
        context['criterias'] = Criteria.objects.filter(problem=self.problem).order_by('order')
        context['alternatives'] = Alternative.objects.filter(problem=self.problem).order_by('order')
        context['alternative_form'] = AlternativeForm(initial={'problem': self.problem.id})
        return context
