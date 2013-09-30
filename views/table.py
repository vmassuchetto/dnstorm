from django.shortcuts import get_object_or_404
from django.views.generic.base import TemplateView

from dnstorm.models import Problem, Idea, Criteria, Alternative, AlternativeItem
from dnstorm.forms import TableTitleForm

from django.utils.translation import ugettext_lazy as _

class TableView(TemplateView):
    template_name = 'table.html'

    def get_context_data(self, *args, **kwargs):
        context = super(TableView, self).get_context_data(**kwargs)
        context['problem'] = get_object_or_404(Problem, id=kwargs['problem'])
        context['ideas'] = Idea.objects.filter(problem=kwargs['problem'])
        context['ideas_modal'] = True
        context['criterias'] = Criteria.objects.filter(problem=kwargs['problem']).order_by('order')
        context['alternatives'] = Alternative.objects.filter(problem=kwargs['problem']).order_by('order')
        context['table_title_form'] = TableTitleForm(initial={'problem': kwargs['problem']})
        return context
