from django.http import Http404, HttpResponse
from django.db.models import Sum
from django.views.generic import View
from django.utils.translation import ugettext_lazy as _

from dnstorm.models import Tag, Vote, Idea
import json

class AjaxView(View):

    def get(self, *args, **kwargs):
        if 'term' in self.request.GET:
            return self.tag_search()
        elif 'idea' and 'weight' in self.request.GET:
            return self.submit_vote()
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

    def submit_vote(self):
        try:
            idea = Idea.objects.get(id=self.request.GET['idea'])
        except:
            raise Http404()
        if idea.user == self.request.user:
            raise Http404()
        weight = int(self.request.GET['weight'])
        weight_choices = [ choice[0] for choice in \
            [ field.choices for field in Vote._meta.fields if field.name == 'weight' ][0] ]
        if weight not in weight_choices:
            raise Http404()
        existing = Vote.objects.filter(idea=idea, user=self.request.user)
        cancel_vote = False
        if len(existing) > 0 and existing[0].weight == weight:
            cancel_vote = True
        existing.delete()
        if not cancel_vote:
            Vote(idea=idea, weight=weight, user=self.request.user).save()
        count = Vote.objects.filter(idea=idea).aggregate(Sum('weight'))['weight__sum']
        return HttpResponse(json.dumps(count if count else 0))

