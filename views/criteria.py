from django.views.generic import TemplateView
from django.utils.translation import ugettext_lazy as _

from dnstorm.models import Criteria

class CriteriaView(TemplateView):
    template_name = 'criteria.html'
    model = Criteria

    def get_context_data(self, *args, **kwargs):
        context = super(CriteriaView, self).get_context_data(**kwargs)
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['criterias'] = Criteria.objects.all()[:30]
        return context

    def get_breadcrumbs(self):
        return [ { 'title': _('Criterias'), 'classes': 'current' } ]
