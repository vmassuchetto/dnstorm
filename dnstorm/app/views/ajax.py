import random
import re

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.urlresolvers import reverse
from django.db.models import Q, Sum
from django.http import Http404, HttpResponse, HttpResponseForbidden, HttpResponseServerError
from django.shortcuts import get_object_or_404
from django.template import loader, Context
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View

from actstream import action
from actstream.models import actor_stream
from actstream.actions import follow, unfollow, is_following
from crispy_forms.utils import render_crispy_form
from notification import models as notification

from dnstorm.app import models
from dnstorm.app import permissions
from dnstorm.app.forms import ProblemForm, IdeaForm, CriteriaForm, CommentForm, ContributorForm
from dnstorm.app.utils import get_object_or_none, email_context, activity_count, activity_reset_counter as _activity_reset_counter

import json

class AjaxView(View):
    """
    Ajax actions view. Will receive all GET and POST requests to /ajax/ URL.
    """

    def get(self, *args, **kwargs):
        """
        Ajax GET requests router.
        """

        if not self.request.is_ajax():
            raise Http404

        # Delete criteria

        if self.request.GET.get('delete_criteria', None):
            return self.delete_criteria()

        # Delete comment

        elif self.request.GET.get('delete_comment', None):
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

        # Reset activity counter

        elif self.request.GET.get('activity_reset_counter', None):
            return self.activity_reset_counter()

        # 'Like' action for an idea

        elif self.request.GET.get('idea_like', None):
            return self.idea_like()

        # 'Like' action for an alternative

        elif self.request.GET.get('alternative_like', None):
            return self.alternative_like()

        # User search

        elif self.request.GET.get('user_search', None):
            return self.user_search()

        # Contributors and invitations management

        elif self.request.GET.get('contributor_add', None):
            return self.contributor_add()

        elif self.request.GET.get('contributor_delete', None):
            return self.contributor_delete()

        # Failure

        return HttpResponseForbidden()

    def post(self, *args, **kwargs):
        """
        Ajax POST requests router.
        """

        if not self.request.is_ajax():
            raise Http404

        # Problem autosave

        if self.request.POST.get('problem_submit', None) \
            and self.request.POST.get('problem_id', None):
            return self.problem_submit()

        # Criteria form submission

        if self.request.POST.get('criteria_submit', None) \
            and self.request.POST.get('problem_id', None):
            return self.criteria_submit()

        # New comment

        elif self.request.POST.get('comment_new', None):
            return self.comment_new()

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

    def user_search(self):
        """
        Will display and invitation button instead of the user result if what's
        being searched is an e-mail.
        """

        if not self.request.user.is_authenticated():
            raise PermissionDenied

        q = self.request.GET.get('user_search', None)
        if not q:
            raise Http404

        result = ''
        e = re.compile('[^@]+@[^@]+\.[^@]+')
        if e.match(q):
            if User.objects.filter(email=q).exists():
                result = loader.render_to_string('user_box.html', {'user': User.objects.filter(email=q)[0]})
            else:
                u = User(username=q, email=q)
                result = loader.render_to_string('user_box.html', {'user': u, 'email_invitation': q})
            return HttpResponse(json.dumps({'result': result}), content_type='application/json')

        for u in User.objects.filter(Q(username__icontains=q) | Q(email__icontains=q))[:10]:
            result += loader.render_to_string('user_box.html', {'user': u})

        return HttpResponse(json.dumps({'result': result}), content_type='application/json')

    def contributor_add(self):
        """
        Adds a user as contributor for a problem.
        """

        # Validation

        user = get_object_or_none(User, username=self.request.GET['contributor_add'])
        problem = get_object_or_404(models.Problem, id=self.request.GET['problem'])
        if not permissions.problem(obj=problem, user=self.request.user, mode='manage'):
            raise PermissionDenied

        # Add contributor

        problem.contributor.add(user)
        follow(user, problem, actor_only=False) if not is_following(user, problem) else None
        result = loader.render_to_string('user_selected.html', {'users': problem.contributor.all()})
        return HttpResponse(json.dumps({'result':result}))

    def contributor_delete(self):
        """
        Removes a user as contributor for a problem.
        """
        # Validation

        user = get_object_or_404(User, username=self.request.GET['contributor_delete'])
        problem = get_object_or_404(models.Problem, id=self.request.GET['problem'])
        if not permissions.problem(obj=problem, user=self.request.user, mode='manage'):
            raise PermissionDenied

        # Remove contributor

        problem.contributor.remove(user)
        unfollow(user, problem)
        result = loader.render_to_string('user_selected.html', {'users': problem.contributor.all()})
        return HttpResponse(json.dumps({'result':result}))

    def invitation_add(self):
        """
        Invites a user to contribute in a problem.
        """

        # Validation

        problem = get_object_or_404(models.Problem, id=self.request.GET['problem'])
        if not permissions.problem(obj=problem, user=self.request.user, mode='manage'):
            raise PermissionDenied

        # Invitations

        for email in self.request.GET.getlist('invitation'):
            if User.objects.filter(email=email).exists() or \
                models.Invitation.objects.filter(email=email).exists():
                continue

            hash = '%032x' % random.getrandbits(128)
            while models.Invitation.objects.filter(hash=hash).exists():
                hash = '%032x' % random.getrandbits(128)
            invitation = models.Invitation.objects.create(problem=problem, email=email, hash=hash)
            u = User.objects.create(username=email, email=email)
            notification.send([u], 'invitation', email_context({ 'invitation': invitation }))
            u.delete()


        # Response

        form = ContributorForm(problem=problem.id)
        return HttpResponse(json.dumps({'form': render_crispy_form(form)}), content_type='application/json')

    def invitation_delete(self):
        """
        Invites a user to contribute in a problem.
        """
        pass

    def activity_reset_counter(self):
        """
        Reset the activity counter.
        """

        if not self.request.user.is_authenticated():
            raise Http404
        _activity_reset_counter(self.request.user)
        return HttpResponse(json.dumps({'ok': 1}), content_type='application/json')

    def criteria_submit(self):
        """
        Submit a criteria for a problem.
        """

        problem = get_object_or_404(models.Problem, id=self.request.POST.get('problem_id'))
        if not permissions.problem(obj=problem, user=self.request.user, mode='manage'):
            raise PermissionDenied

        obj = get_object_or_none(models.Criteria, id=self.request.POST.get('id', None))
        if obj and not permissions.problem(obj=obj.problem, user=self.request.user, mode='manage'):
            raise PermissionDenied

        self.request.POST = self.request.POST.copy()
        self.request.POST['author'] = self.request.user.id
        self.request.POST['description'] = self.request.POST['criteria_description']
        criteria = CriteriaForm(self.request.POST)

        criteria.instance = obj if obj else criteria.instance
        criteria.instance.problem = problem
        if not criteria.is_valid():
            return HttpResponse(json.dumps({'errors':dict(criteria.errors)}), content_type='application/json')
        criteria.save()

        criteria.instance.fill_data()
        result = loader.render_to_string('criteria_row.html', {'criteria': criteria.instance, 'criteria_form': criteria})
        return HttpResponse(json.dumps({'result': result}), content_type='application/json')

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
            'html': loader.render_to_string('alternative_row.html', {
                'alternative': a,
                'problem_perm_manage': True
            })
        }
        return HttpResponse(json.dumps(response), content_type='application/json')

    def comment_new(self):
        """
        Create a new comment on a problem or idea.
        """

        # Start object

        content = self.request.POST.get('content', None)
        if not content:
            raise Http404
        comment = models.Comment(content=content, author=self.request.user)

        # Validation

        problem = self.request.POST.get('problem', None)
        if problem:
            _obj = get_object_or_none(models.Problem, id=problem)
            comment.problem = _obj
            _problem = _obj
            target = '#comments-problem-%d' % _obj.id
        criteria = self.request.POST.get('criteria', None)
        if criteria:
            _obj = get_object_or_none(models.Criteria, id=criteria)
            comment.criteria = _obj
            _problem = _obj.problem
            target = '#comments-criteria-%d' % _obj.id
        idea = self.request.POST.get('idea', None)
        if idea:
            _obj = get_object_or_none(models.Idea, id=idea)
            comment.idea = _obj
            _problem = _obj.problem
            target = '#comments-idea-%d' % _obj.id
        alternative = self.request.POST.get('alternative', None)
        if alternative:
            _obj = get_object_or_none(models.Alternative, id=alternative)
            comment.alternative = _obj
            _problem = _obj.problem
            target = '#comments-alternative-%d' % _obj.id
        if not problem and not idea and not criteria and not alternative:
            raise Http404

        # Check permissions

        if not permissions.problem(obj=_problem, user=self.request.user, mode='contribute'):
            raise PermissionDenied

        # Save comment

        comment.save()
        comment.perm_edit = permissions.problem(obj=_problem, user=self.request.user, mode='manage')

        # Action

        follow(self.request.user, _problem, actor_only=False) if not is_following(self.request.user, _problem) else None
        a = action.send(self.request.user, verb='commented', action_object=_obj, target=_problem)
        a[0][1].data = {'diff': content}
        a[0][1].save()
        activity_count(_problem)

        # Response

        t = loader.get_template('comment.html')
        c = Context({'comment': comment})
        return HttpResponse(json.dumps({'target': target, 'html': re.sub("\n", '', t.render(c))}), content_type='application/json')

    def delete_criteria(self):
        """
        Delete criteria from the problem form.
        """
        c = get_object_or_404(models.Criteria, id=self.request.GET.get('delete_criteria'))
        if not c or not self.request.user.is_authenticated() or 'on' != self.request.GET.get('yes', None):
            raise Http404
        if not permissions.problem(obj=c.problem, user=self.request.user, mode='manage'):
            raise PermissionDenied
        deleted_id = c.id
        c.delete()
        response = {
            'deleted': deleted_id
        }
        return HttpResponse(json.dumps(response), content_type='application/json')

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

        # Validation

        alternative = get_object_or_404(models.Alternative, id=self.request.POST.get('alternative', None))
        if not permissions.problem(obj=alternative.problem, user=self.request.user, mode='manage'):
            return HttpResponseForbidden()

        # Select idea

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

        # Response

        response = {'html': loader.render_to_string('alternative_row.html', {
            'alternative': alternative,
            'problem_perm_manage': True})}
        return HttpResponse(json.dumps(response), content_type='application/json')

    def resend_invitation(self):
        """
        Resend an invitation.
        """

        # Validation

        invitation = get_object_or_404(models.Invitation, id=self.request.GET.get('resend_invitation', None))
        if not permissions.problem(obj=invitation.problem, user=self.request.user, mode='manage'):
            raise PermissionDenied
        u = User.objects.create(username=invitation.email, email=invitation.email)
        notification.send([u], 'invitation', email_context({ 'invitation': invitation }))
        u.delete()
        return HttpResponse(1)

    def delete_invitation(self):
        """
        Deletes an invitation.
        """

        # Validation

        invitation = get_object_or_404(models.Invitation, id=self.request.GET.get('delete_invitation', None))
        if not permissions.problem(obj=invitation.problem, user=self.request.user, mode='manage'):
            return HttpResponseForbidden()


        invitation.delete()
        return HttpResponse()

    def idea_like(self):
        """
        Performs a 'like' and 'unlike' action on an idea.
        """

        idea = get_object_or_404(models.Idea, id=self.request.GET.get('idea_like', None))
        if not permissions.idea(obj=idea, user=self.request.user, mode='contribute'):
            return HttpResponseForbidden()

        if models.Vote.objects.filter(idea=idea, author=self.request.user).exists():
            models.Vote.objects.filter(idea=idea, author=self.request.user).delete()
            voted = False
        else:
            models.Vote.objects.create(idea=idea, author=self.request.user)
            voted = True

        response = {'counter': idea.vote_count(), 'voted': voted}
        return HttpResponse(json.dumps(response), content_type='application/json')

    def alternative_like(self):
        """
        Performs a 'like' and 'unlike' action on an alternative.
        """

        alternative = get_object_or_404(models.Alternative, id=self.request.GET.get('alternative_like', None))
        if not permissions.problem(obj=alternative.problem, user=self.request.user, mode='contribute'):
            return HttpResponseForbidden()

        if models.Vote.objects.filter(alternative=alternative, author=self.request.user).exists():
            models.Vote.objects.filter(alternative=alternative, author=self.request.user).delete()
            voted = False
        else:
            models.Vote.objects.create(alternative=alternative, author=self.request.user)
            voted = True

        response = {'counter': alternative.vote_count(), 'voted': voted}
        return HttpResponse(json.dumps(response), content_type='application/json')

