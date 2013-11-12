from django.views.generic import TemplateView

from dnstorm.models import Criteria

class CriteriaView(TemplateView):
    template_name = 'criteria.html'
    model = Criteria

    def get_context_data(self, *args, **kwargs):
        context = super(CriteriaView, self).get_context_data(**kwargs)
        context['criterias'] = Criteria.objects.all()[:30]
        return context
