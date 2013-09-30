from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.db.models import Sum
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import View
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404
from django.template import loader, Context

from dnstorm.models import Problem, Tag, Vote, Idea, Comment, Criteria, Alternative, AlternativeItem
import json

class AjaxView(View):

    def get(self, *args, **kwargs):

        # Search for tags

        if 'term' in self.request.GET:
            return self.tag_search()

        # Vote

        elif 'idea' and 'weight' in self.request.GET:
            return self.submit_vote()

        # Delete comments

        elif 'delete_comment' in self.request.GET:
            return self.delete_comment()

        # Failure

        return HttpResponseForbidden()

    def post(self, *args, **kwargs):

        # New comment

        if 'idea' and 'content' in self.request.POST:
            return self.submit_comment()

        # New criteria

        elif 'mode' in self.request.POST and 'criteria' == self.request.POST['mode'] \
            and 'object' in self.request.POST and 'new' == self.request.POST['object']:
            return self.table_new_criteria()

        # New alternative

        elif 'mode' in self.request.POST and 'alternative' == self.request.POST['mode'] \
            and 'object' in self.request.POST and 'new' == self.request.POST['object']:
            return self.table_new_alternative()

        # New item

        elif 'alternative' in self.request.POST \
            and 'criteria' in self.request.POST \
            and 'idea' in self.request.POST:
            return self.table_new_item()

        # Failure

        return HttpResponseForbidden()

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
        idea = get_object_or_404(Idea, pk=self.request.GET['idea'])
        if not self.request.user.is_authenticated() or idea.user == self.request.user:
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

    def submit_comment(self):
        idea = get_object_or_404(Idea, pk=self.request.POST['idea'])
        content = self.request.POST['content']
        comment = Comment(idea=idea, content=content, author=self.request.user)
        comment.save()
        t = loader.get_template('comment.html')
        c = Context({'comment': comment})
        return HttpResponse(t.render(c))

    def delete_comment(self):
        try:
            Comment.objects.get(pk=self.request.GET['delete_comment']).delete()
            result = 1
        except ObjectDoesNotExist:
            result = 0
        return HttpResponse(result)

    def table_new_criteria(self):
        p = Problem.objects.get(pk=self.request.POST['problem'])
        n = Criteria.objects.filter(problem=self.request.POST['problem']).count()
        criteria = Criteria(
            problem=p,
            title=self.request.POST['title'],
            description=self.request.POST['description'],
            order = n)
        criteria.save()
        output = {
            'id': criteria.id,
            'title': criteria.title,
            'description': criteria.description
        }
        return HttpResponse(json.dumps(output))

    def table_new_alternative(self):
        p = Problem.objects.get(pk=self.request.POST['problem'])
        n = Alternative.objects.filter(problem=self.request.POST['problem']).count()
        alternative = Alternative(
            problem=p,
            title=self.request.POST['title'],
            description=self.request.POST['description'],
            order = n)
        alternative.save()
        output = {
            'id': alternative.id,
            'title': alternative.title,
            'description': alternative.description
        }
        return HttpResponse(json.dumps(output))

    def table_new_item(self):
        c = Criteria.objects.get(pk=self.request.POST['criteria'])
        a = Alternative.objects.get(pk=self.request.POST['alternative'])
        i = Idea.objects.get(pk=self.request.POST['idea'])
        item = AlternativeItem(criteria=c, alternative=a, idea=i)
        item.save()
        output = { 'id': i.id  }
        return HttpResponse(json.dumps(output))
