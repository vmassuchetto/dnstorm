import re

from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.db.models import Sum
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import View
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404
from django.template import loader, Context

from app.models import Problem, Criteria, Vote, Idea, Comment, Alternative, AlternativeItem
from app.forms import CriteriaForm

from app.lib.slug import unique_slugify
from app.lib.utils import get_object_or_none

import json

class AjaxView(View):

    def get(self, *args, **kwargs):

        # Search for criterias in problem edition

        if 'term' in self.request.GET:
            return self.problem_criteria_search()

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

        if 'idea' and 'content' in self.request.POST or \
            'problem' and 'content' in self.request.POST:
            return self.submit_comment()

        # New criteria in problem edition

        elif 'mode' in self.request.POST and 'problem_criteria_create' == self.request.POST['mode'] \
            and 'name' in self.request.POST and 'description' in self.request.POST:
            return self.problem_criteria_create()

        # New criteria

        elif 'mode' in self.request.POST and 'criteria' == self.request.POST['mode'] \
            and 'object' in self.request.POST and 'new' == self.request.POST['object']:
            return self.table_new_criteria()

        # New alternative

        elif 'mode' in self.request.POST and 'alternative' == self.request.POST['mode'] \
            and 'object' in self.request.POST and 'new' == self.request.POST['object']:
            return self.table_new_alternative()

        # Remove alternative

        elif 'mode' in self.request.POST and 'remove-alternative' == self.request.POST['mode'] \
            and 'object' in self.request.POST:
            return self.table_remove_alternative()

        # New alternative item

        elif 'alternative' in self.request.POST \
            and 'criteria' in self.request.POST \
            and self.has_regex_key('idea\[[0-9]+\]', dict(self.request.POST.iterlists())):
            return self.table_new_item()

        # Failure

        return HttpResponseForbidden()

    def has_regex_key(self, regex, dictionary):
        r = re.compile(regex)
        for key in dictionary:
            if r.match(key):
                return True
        return False

    def problem_criteria_search(self):
        criterias = Criteria.objects.filter(slug__icontains = self.request.GET['term'])[:5]
        response = []
        for c in criterias:
            response.append({
                'id': c.id,
                'label': c.name,
                'description': c.description
            })
        return HttpResponse(json.dumps(response), content_type="application/json")

    def problem_criteria_create(self):
        criteria = CriteriaForm(self.request.POST)
        if criteria.is_valid():
            c = criteria.save()
            response = {
                'id': c.id,
                'name': c.name,
                'parent': c.parent.name,
                'description': c.description
            }
        else:
            response = { 'errors': criteria.errors }
        return HttpResponse(json.dumps(response), content_type="application/json")

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
        return HttpResponse(json.dumps(count if count else 0), content_type="application/json")

    def submit_comment(self):
        try:
            problem = get_object_or_none(Problem, id=int(self.request.POST['problem']))
        except ValueError:
            problem = None
        try:
            idea = get_object_or_none(Idea, id=int(self.request.POST['idea']))
        except ValueError:
            idea = None
        content = self.request.POST['content']
        comment = Comment(problem=problem, idea=idea, content=content, author=self.request.user)
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

    def table_new_alternative(self):
        p = Problem.objects.get(pk=self.request.POST['problem'])
        n = Alternative.objects.filter(problem=self.request.POST['problem']).count()
        alternative = Alternative(
            problem=p,
            name=self.request.POST['name'],
            description=self.request.POST['description'],
            order = n)
        alternative.save()
        output = {
            'id': alternative.id,
            'name': alternative.name,
            'description': alternative.description
        }
        return HttpResponse(json.dumps(output), content_type="application/json")

    def table_remove_alternative(self):
        a = Alternative.objects.get(id=int(self.request.POST['object']))
        AlternativeItem.objects.filter(alternative=a).delete()
        a.delete()
        output = {
            'deleted': a.id
        }
        return HttpResponse(json.dumps(output), content_type='application/json')

    def table_new_item(self):
        ideas = list()
        r = re.compile('idea\[[0-9]+\]')
        for key in self.request.POST:
            if r.match(key) and int(self.request.POST[key]):
                ideas.append(int(self.request.POST[key]))
        if not len(ideas):
            raise Http404

        c = None if not int(self.request.POST['criteria']) else Criteria.objects.get(pk=self.request.POST['criteria'])
        a = Alternative.objects.get(pk=self.request.POST['alternative'])
        ideas = Idea.objects.filter(id__in=ideas)
        try:
            item = AlternativeItem.objects.get(criteria=c, alternative=a)
            item.idea.clear()
        except:
            item = AlternativeItem(criteria=c, alternative=a)
        item.save()
        for i in ideas:
            item.idea.add(i)
        item.save()

        output = list()
        for i in ideas:
            output.append({
                'id': i.id,
                'title': i.title
            });
        return HttpResponse(json.dumps(output), content_type="application/json")
