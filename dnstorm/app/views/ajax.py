import re

from django.contrib.auth.models import User
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.db.models import Sum
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.views.generic import View
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404
from django.template import loader, Context

from crispy_forms.utils import render_crispy_form
from notification import models as notification
from actstream import action
from actstream.models import followers
from actstream.actions import follow

from dnstorm.app import models
from dnstorm.app.forms import IdeaForm, CriteriaForm, CommentForm
from dnstorm.app.views.idea import idea_save
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

        # Resend invitation

        elif self.request.GET.get('resend_invitation', None):
            return self.resend_invitation()

        # Delete invitation

        elif self.request.GET.get('delete_invitation', None):
            return self.delete_invitation()

        # Failure

        return HttpResponseForbidden()

    def post(self, *args, **kwargs):
        """
        Ajax POST requests router.
        """

        # New idea on problems

        if self.request.POST.get('new_idea', None):
            return self.new_idea()

        # New criteria on problem form

        elif self.request.POST.get('new_criteria', None):
            return self.new_criteria()

        # New comment

        elif self.request.POST.get('new_comment', None):
            return self.new_comment()

        # Add ideas to some alternative

        elif self.request.POST.get('alternative', None) \
            and self.request.POST.get('idea_alternative', None):
            return self.idea_alternative()

        # Failure

        return HttpResponseForbidden()

    def has_regex_key(self, regex, dictionary):
        """
        Tests for a key in a dictionary.
        """
        r = re.compile(regex)
        for key in dictionary:
            if r.match(key):
                return True
        return False

    def new_idea(self):
        """
        Create a new idea.
        """
        if not self.request.user.is_authenticated():
            raise Http404
        idea = IdeaForm(self.request.POST)
        if not permissions.problem(obj=idea.problem, user=self.request.user, mode='contribute'):
            raise PermissionDenied
        if not idea.is_valid():
            return HttpResponse(json.dumps({'errors': dict(idea.errors)}), content_type='application/json')
        idea.instance.problem = idea.problem
        idea.instance.request = self.request
        idea = idea_save(idea.instance, idea, 'obj')
        idea.fill_data()
        idea.comment_form = CommentForm()
        t = loader.get_template('idea.html')
        c = Context({
            'idea': idea,
            'idea_actions': True,
            'problem_perm_contribute': True
        })
        return HttpResponse(json.dumps({
            'id': idea.id,
            'html': t.render(c)
        }), content_type='application/json')

    def new_criteria(self):
        """
        Create a new criteria.
        """
        if not self.request.user.is_authenticated():
            raise Http404
        criteria = CriteriaForm(self.request.POST)
        if not criteria.is_valid():
            return HttpResponse(json.dumps({'errors':dict(criteria.errors)}), content_type='application/json')
        criteria.save()
        t = loader.get_template('criteria_lookup_display.html')
        c = Context({'criteria': criteria.instance})
        return HttpResponse(json.dumps({
            'id': criteria.instance.id,
            'lookup_display': t.render(c)
        }), content_type='application/json')

    def new_alternative(self):
        """
        Create a new alternative.
        """
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
            'html': loader.render_to_string('alternative.html', {
                'alternative': a,
                'problem_perm_manage': True
            })
        }
        return HttpResponse(json.dumps(response), content_type='application/json')

    def new_comment(self):
        """
        Create a new comment.
        """
        problem = self.request.POST.get('problem', None)
        if problem:
            problem = get_object_or_none(models.Problem, id=problem)
        idea = self.request.POST.get('idea', None)
        if idea:
            idea = get_object_or_none(models.Idea, id=idea)
        if not problem and not idea:
            raise Http404
        _problem = problem if problem else idea.problem
        if not permissions.problem(obj=_problem, user=self.request.user, mode='contribute'):
            raise PermissionDenied
        content = self.request.POST.get('content', None)
        if not content:
            raise Http404

        comment = models.Comment(content=content, author=self.request.user)
        target = False
        if problem:
            obj = problem
            comment.problem = problem
            target = 'div#comments-problem-' + str(problem.id)
        if idea:
            obj = idea
            comment.idea = idea
            target = 'div#comments-idea-' + str(idea.id)
        comment.save()

        # Send an action and follow the problem

        action.send(self.request.user, verb='commented', action_object=obj, target=_problem)
        follow(self.request.user, _problem) if self.request.user not in followers(_problem) else None

        comment.perm_edit = permissions.problem(obj=_problem, user=self.request.user, mode='manage')
        t = loader.get_template('comment.html')
        c = Context({'comment': comment})
        return HttpResponse(json.dumps({'target': target, 'html': re.sub("\n", '', t.render(c))}), content_type='application/json')

    def delete_comment(self):
        """
        Delete a comment. This is actually a delete toggle. It will delete over
        undeleted, and undelete over deleted items.
        """
        comment = get_object_or_none(models.Comment, id=int(self.request.GET['delete_comment']))
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

    def delete_alternative(self):
        """
        Delete alternative.
        """
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
        """
        Vote for an alternative.
        """
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
        """
        Select an idea for an alternative.
        """
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
            'html': loader.render_to_string('alternative.html', {
                'alternative': alternative,
                'problem_perm_manage': True
            })
        }
        return HttpResponse(json.dumps(response), content_type='application/json')

    def delete_idea(self):
        """
        Delete an idea. This is actually a delete toggle. It will delete over
        undeleted, and undelete over deleted items.
        """
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

    def resend_invitation(self):
        """
        Resends an invitation.
        """
        invitation = get_object_or_404(models.Invitation, id=self.request.GET.get('resend_invitation', None))
        if not permissions.problem(obj=invitation.problem, user=self.request.user, mode='manage'):
            raise PermissionDenied
        fake_user = User(id=1, username='any', email=invitation.email)
        from_user = invitation.problem.author.get_full_name() if invitation.problem.author.get_full_name() else invitation.problem.author.username
        notification.send([fake_user], 'invitation', { 'from_user': from_user, 'problem': invitation.problem })
        return HttpResponse(1)

    def delete_invitation(self):
        """
        Deletes an invitation.
        """
        invitation = get_object_or_404(models.Invitation, id=self.request.GET.get('delete_invitation', None))
        if not permissions.problem(obj=invitation.problem, user=self.request.user, mode='manage'):
            raise PermissionDenied
        invitation.delete()
        return HttpResponse(1)

