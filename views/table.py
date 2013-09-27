from django.shortcuts import get_object_or_404
from django.views.generic.base import TemplateView

from dnstorm.models import Problem

class TableView(TemplateView):
    template_name = 'table.html'

    def get_context_data(self, *args, **kwargs):
        context = super(TableView, self).get_context_data(**kwargs)
        context['problem'] = get_object_or_404(Problem, id=kwargs['problem'])
        return context
