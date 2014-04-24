import re

from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.db.models import Sum
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.views.generic import View
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404
from django.template import loader, Context

from dnstorm.app.models import Problem, Criteria, Vote, Idea, Comment, Alternative, AlternativeItem
from dnstorm.app.forms import CriteriaForm

from dnstorm.app import permissions
from dnstorm.app.lib.slug import unique_slugify
from dnstorm.app.lib.utils import get_object_or_none

import json

class AjaxView(View):

    def get(self, *args, **kwargs):

        # Search for criterias in problem edition

        if self.request.GET.get('term', None):
            return self.problem_criteria_search()

        # Vote for idea

        elif self.request.GET.get('idea', None) \
            and self.request.GET.get('weight', None):
            return self.submit_idea_vote()

        # Vote for alternative

        elif self.request.GET.get('alternative', None) \
            and self.request.GET.get('weight', None):
            return self.submit_alternative_vote()

        # Delete comments

        elif self.request.GET.get('delete_comment', None):
            return self.delete_comment()

        # Delete idea

        elif self.request.GET.get('delete_idea', None):
            return self.delete_idea()

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
            and 'criteria' in self.request.POST:
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
                'parent': c.parent.name if c.parent else '',
                'description': c.description
            }
        else:
            response = { 'errors': criteria.errors }
        return HttpResponse(json.dumps(response), content_type="application/json")

    def submit_idea_vote(self):
        idea = get_object_or_404(Idea, pk=self.request.GET['idea'])
        if not self.request.user.is_authenticated() \
            or idea.author == self.request.user \
            or not permissions.problem(obj=idea.problem, user=self.request.user, mode='contribute'):
            raise PermissionDenied
        weight = int(self.request.GET['weight'])
        weight_choices = [ choice[0] for choice in \
            [ field.choices for field in Vote._meta.fields if field.name == 'weight' ][0] ]
        if weight not in weight_choices:
            raise Http404()
        existing = Vote.objects.filter(idea=idea, author=self.request.user)
        cancel_vote = False
        if len(existing) > 0 and existing[0].weight == weight:
            cancel_vote = True
        existing.delete()
        if not cancel_vote:
            Vote(idea=idea, weight=weight, author=self.request.user).save()
        count = Vote.objects.filter(idea=idea).aggregate(Sum('weight'))['weight__sum']
        return HttpResponse(json.dumps(count if count else 0), content_type="application/json")

    def submit_alternative_vote(self):
        alternative = get_object_or_404(Alternative, pk=self.request.GET['alternative'])
        if not self.request.user.is_authenticated() \
            or not permissions.problem(obj=alternative.problem, user=self.request.user, mode='contribute'):
            raise PermissionDenied
        weight = int(self.request.GET['weight'])
        vote = Vote.objects.filter(alternative=alternative, author=self.request.user)
        if weight <= 0:
            vote.delete()

            response = 0
        elif weight == 1 and len(vote) > 0:
            response = 1
        elif weight == 1 and len(vote) == 0:
            Vote(alternative=alternative, author=self.request.user, weight=1).save()
            response = 1
        return HttpResponse(json.dumps(response), content_type="application/json")

    def submit_comment(self):
        try:
            problem = get_object_or_none(Problem, id=int(self.request.POST['problem']))
        except ValueError:
            problem = None
        try:
            idea = get_object_or_none(Idea, id=int(self.request.POST['idea']))
        except ValueError:
            idea = None
        # TODO
        if not permissions.problem(obj=problem, user=self.request.user, mode='contribute'):
            raise PermissionDenied
        content = self.request.POST['content']
        comment = Comment(problem=problem, idea=idea, content=content, author=self.request.user)
        comment.save()
        t = loader.get_template('comment.html')
        c = Context({'comment': comment})
        return HttpResponse(t.render(c))

    def delete_comment(self):
        '''This is actually a delete toggle. It will delete over undeleted, and
        undelete over deleted items.'''
        comment = get_object_or_none(Comment, id=int(self.request.GET['delete_comment']))
        mode = 'undelete' if comment.deleted_by else 'delete'
        if not comment or not permissions.comment(obj=comment, user=self.request.user, mode=mode):
            return HttpResponse(0)
        if comment.deleted_by:
            comment.deleted_by = None
            response_mode = 'delete'
        else:
            comment.deleted_by = self.request.user
            response_mode = 'undelete'
        comment.save()
        return HttpResponse(response_mode)

    def delete_idea(self):
        '''This is actually a delete toggle. It will delete over undeleted, and
        undelete over deleted items.'''
        idea = get_object_or_none(Idea, id=int(self.request.GET['delete_idea']))
        mode = 'undelete' if idea.deleted_by else 'delete'
        if not idea or not permissions.idea(obj=idea, user=self.request.user, mode=mode):
            return HttpResponse(unmode)
        if idea.deleted_by:
            idea.deleted_by = None
            response_mode = 'delete'
        else:
            idea.deleted_by = self.request.user
            response_mode = 'undelete'
        idea.save()
        return HttpResponse(response_mode)

    def table_new_alternative(self):
        p = Problem.objects.get(pk=self.request.POST['problem'])
        n = Alternative.objects.filter(problem=self.request.POST['problem']).count()
        alternative = Alternative(
            problem=p,
            name=self.request.POST['name'],
            description=self.request.POST['description'],
            order=n)
        alternative.save()
        output = {
            'id': alternative.id,
            'name': alternative.name,
            'description': alternative.description,
            'problem': p.id
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

        # Get the base item and clear it

        c = None if not int(self.request.POST['criteria']) else Criteria.objects.get(pk=self.request.POST['criteria'])
        a = Alternative.objects.get(pk=self.request.POST['alternative'])
        try:
            item = AlternativeItem.objects.get(criteria=c, alternative=a)
            item.idea.clear()
        except:
            item = AlternativeItem(criteria=c, alternative=a)
        item.save()

        # When submitting empty queries just clear the item and exit

        if not self.has_regex_key('idea\[[0-9]+\]', dict(self.request.POST.iterlists())):
            return HttpResponse(json.dumps([]), content_type="application/json")

        ideas = list()
        r = re.compile('idea\[[0-9]+\]')
        for key in self.request.POST:
            if r.match(key) and int(self.request.POST[key]):
                ideas.append(int(self.request.POST[key]))
        if not len(ideas):
            raise Http404

        ideas = Idea.objects.filter(id__in=ideas)
        for i in ideas:
            item.idea.add(i)
        item.save()

        output = dict()

        output['ideas'] = list()
        for i in ideas:
            output['ideas'].append({
                'id': i.id,
                'title': i.title,
                'problem': i.problem.id,
                'criteria': c.id if c else None,
                'alternative': a.id
            })

        output['quantifiers'] = list()
        for q in a.get_quantifiers().values():
            output['quantifiers'].append({
                'id': q.id,
                'name': q.name,
                'value': q.value,
                'format': q.format
            })

        return HttpResponse(json.dumps(output), content_type="application/json")
