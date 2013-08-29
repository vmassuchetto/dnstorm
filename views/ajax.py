from django.http import HttpResponse
from django.views.generic import View
from django.utils.translation import ugettext_lazy as _

from dnstorm.models import Tag
import json

class AjaxView(View):

    def get(self, *args, **kwargs):
        if self.request.GET.has_key('term'):
            return self.tag_search()
        return HttpResponse(_('Invalid request'))

    def tag_search(self):
        tags = Tag.objects.filter(slug__icontains = self.request.GET['term'])[:5]
        response = []
        for t in tags:
            response.append({
                'id': t.id,
                'label': t.name,
                'description': t.description
            })
        return HttpResponse(json.dumps(response, sort_keys=True))
