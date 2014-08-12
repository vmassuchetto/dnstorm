import re

from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.db.models import Sum
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.views.generic import View
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404
from django.template import loader, Context

from crispy_forms.utils import render_crispy_form

from dnstorm.app import models
from dnstorm.app.forms import CriteriaForm

from dnstorm.app import permissions
from dnstorm.app.lib.utils import get_object_or_none

import json

class AjaxView(View):
    """
    Ajax actions view. Will receive all GET and POST requests to /ajax/ URL.
    """

    def get(self, *args, **kwargs):
        """
        Ajax GET requests router.
        """

        # Delete comment

        if self.request.GET.get('delete_comment', None):
            return self.delete_comment()

        # Delete idea

        elif self.request.GET.get('delete_idea', None):
            return self.delete_idea()

        # New alternative

        elif self.request.GET.get('new_alternative', None) \
            and self.request.GET.get('problem', None):
            return self.new_alternative()

        # Delete alternative

        elif self.request.GET.get('delete_alternative', None):
            return self.delete_alternative()

        # Alternative vote

        elif self.request.GET.get('vote_alternative', None):
            return self.vote_alternative()

        # Failure

        return HttpResponseForbidden()

    def post(self, *args, **kwargs):
        """
        Ajax POST requests router.
        """

        # New comment

        if 'idea' and 'content' in self.request.POST or \
            'problem' and 'content' in self.request.POST:
            return self.submit_comment()

        # Add ideas to some alternative

        elif self.request.POST.get('alternative', None) \
            and self.request.POST.get('idea_alternative', None):
            return self.idea_alternative()

        # Failure

        return HttpResponseForbidden()

    def has_regex_key(self, regex, dictionary):
        r = re.compile(regex)
        for key in dictionary:
            if r.match(key):
                return True
        return False

    def new_alternative(self):
        problem = get_object_or_404(models.Problem, id=self.request.GET['problem'])
        if not problem or not self.request.user.is_authenticated():
            raise Http404
        if not permissions.problem(obj=problem, user=self.request.user, mode='manage'):
            raise PermissionDenied
        order = models.Alternative.objects.filter(problem=problem).count() + 1
        a = models.Alternative(problem=problem, order=order)
        a.save()
        a.fill_data()
        response = {
            'id': a.id,
            'html': loader.render_to_string('problem_alternative.html', {
                'alternative': a,
                'problem_perm_manage': True
            })
        }
        return HttpResponse(json.dumps(response), content_type='application/json')

    def delete_alternative(self):
        a = get_object_or_404(models.Alternative, id=self.request.GET.get('delete_alternative'))
        if not a or not self.request.user.is_authenticated():
            raise Http404
        if not permissions.problem(obj=a.problem, user=self.request.user, mode='manage'):
            raise PermissionDenied
        deleted_id = a.id
        problem = a.problem
        a.delete()
        # Reorder the remaining alternatives
        i = 0
        for a in models.Alternative.objects.filter(problem=problem).order_by('order'):
            i += 1
            a.order = i
            a.save()
        response = {
            'deleted': deleted_id
        }
        return HttpResponse(json.dumps(response), content_type='application/json')

    def vote_alternative(self):
        a = get_object_or_404(models.Alternative, id=self.request.GET.get('vote_alternative'))
        if not a or not self.request.user.is_authenticated():
            raise Http404
        vote = models.Vote.objects.filter(alternative=a, author=self.request.user)
        if len(vote) > 0:
            vote.delete()
            voted = False
        else:
            models.Vote(alternative=a, author=self.request.user).save()
            voted = True
        votes = models.Vote.objects.filter(alternative=a).count()
        response = {'votes': votes, 'voted': voted}
        return HttpResponse(json.dumps(response), content_type='application/json')

    def idea_alternative(self):
        alternative = get_object_or_404(models.Alternative, id=self.request.POST.get('alternative'))
        if not alternative or not self.request.user.is_authenticated():
            raise Http404
        if not permissions.problem(obj=alternative.problem, user=self.request.user, mode='manage'):
            raise PermissionDenied
        alternative.idea.clear()
        ideas = list()
        r = re.compile('idea\[[0-9]+\]')
        for key in self.request.POST:
            if r.match(key) and int(self.request.POST[key]):
                ideas.append(int(self.request.POST[key]))
        for i in ideas:
            alternative.idea.add(i)
        alternative.save()
        alternative.fill_data()
        response = {
            'html': loader.render_to_string('problem_alternative.html', {
                'alternative': alternative,
                'problem_perm_manage': True
            })
        }
        return HttpResponse(json.dumps(response), content_type='application/json')

    def submit_comment(self):
        try:
            problem = get_object_or_none(models.Problem, id=int(self.request.POST['problem']))
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
        if not comment:
            raise Http404
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
        if not idea:
            raise Http404
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
