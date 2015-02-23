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
from dnstorm.app.forms import ProblemForm, IdeaForm, CriteriaForm, CommentForm
from dnstorm.app.utils import get_object_or_none, email_context, activity_count, activity_register, activity_reset_counter as _activity_reset_counter, is_email

import json

class AjaxView(View):
    """
    Ajax actions view. Will receive all GET and POST requests to /ajax/ URL.
    """

    def get(self, *args, **kwargs):
        """
        Ajax GET requests router.
        """
        # Validation
        if not self.request.is_ajax():
            raise Http404

        # Delete
        # criteria
        if self.request.GET.get('delete_criteria', None):
            return self.delete_criteria()
        # idea
        elif self.request.GET.get('delete_idea', None):
            return self.delete_idea()
        # alternative
        elif self.request.GET.get('delete_alternative', None):
            return self.delete_alternative()
        # contributor
        elif self.request.GET.get('contributor_delete', None):
            return self.contributor_delete()

        # Create
        # alternative
        elif self.request.GET.get('new_alternative', None) \
            and self.request.GET.get('problem', None):
            return self.new_alternative()
        elif self.request.GET.get('vote_alternative', None):
            return self.vote_alternative()
        # idea
        elif self.request.GET.get('idea_like', None):
            return self.idea_like()
        # alternative
        elif self.request.GET.get('alternative_like', None):
            return self.alternative_like()
        # activity
        elif self.request.GET.get('activity_reset_counter', None):
            return self.activity_reset_counter()
        # contributor
        elif self.request.GET.get('contributor_add', None):
            return self.contributor_add()

        # Get
        # users
        elif self.request.GET.get('user_search', None):
            return self.user_search()

        # Failure
        return HttpResponseForbidden()

    def post(self, *args, **kwargs):
        """
        Ajax POST requests router.
        """
        # Validation
        if not self.request.is_ajax():
            raise Http404

        # Problem
        # criteria form submission
        if self.request.POST.get('criteria_submit', None) \
            and self.request.POST.get('problem_id', None):
            return self.criteria_submit()

        # Alternative
        # put an idea in an alternative
        elif self.request.POST.get('alternative', None) \
            and self.request.POST.get('idea_alternative', None):
            return self.idea_alternative()

        # Comment
        elif self.request.POST.get('comment_new', None):
            return self.comment_new()

        # Failure
        return HttpResponseForbidden()

    def user_search(self):
        """
        Will display an invitation button instead of the user result if what's
        being searched is an e-mail.
        """
        # Validation
        if not self.request.user.is_authenticated():
            raise PermissionDenied
        q = self.request.GET.get('user_search', None)
        if not q:
            raise Http404

        # Response
        result = ''
        if is_email(q):
            if User.objects.filter(email=q).exists():
                result = loader.render_to_string('item_user.html', {'user': User.objects.filter(email=q)[0], 'enclosed': True})
            else:
                u = User(username=q, email=q)
                result = loader.render_to_string('item_user.html', {'user': u, 'email_invitation': q, 'enclosed': True})
            return HttpResponse(json.dumps({'result': result}), content_type='application/json')

        for u in User.objects.filter(Q(username__icontains=q) | Q(email__icontains=q))[:10]:
            result += loader.render_to_string('item_user.html', {'user': u, 'enclosed': True})

        return HttpResponse(json.dumps({'result': result}), content_type='application/json')

    def contributor_add(self):
        """
        Add a user as contributor for a problem.
        """
        # Validation
        user = get_object_or_none(User, username=self.request.GET['contributor_add'])
        problem = get_object_or_404(models.Problem, id=self.request.GET['problem'])
        if not permissions.problem(obj=problem, user=self.request.user, mode='manage'):
            raise PermissionDenied

        # Commit
        # invitation
        if not user and is_email(self.request.GET['contributor_add']):
            return self.invitation_add()
        # contributor
        problem.contributor.add(user)
        follow(user, problem, actor_only=False) if not is_following(user, problem) else None

        # Response
        result = loader.render_to_string('_update_problem_users.html', {'users': problem.contributor.order_by('first_name')})
        return HttpResponse(json.dumps({'result': result}), content_type='application/json')

    def contributor_delete(self):
        """
        Removes a user as contributor for a problem.
        """
        # Validation
        user = get_object_or_404(User, username=self.request.GET['contributor_delete'])
        problem = get_object_or_404(models.Problem, id=self.request.GET['problem'])
        if not permissions.problem(obj=problem, user=self.request.user, mode='manage'):
            raise PermissionDenied

        # Commit
        problem.contributor.remove(user)
        unfollow(user, problem)
        # delete user and invitations if there's no other invitation
        if not models.Problem.objects.filter(contributor__in=[user]).exists():
            user.delete()
            models.Invitation.objects.filter(user=user).delete()

        # Response
        result = loader.render_to_string('_update_problem_users.html', {'users': problem.contributor.order_by('first_name')})
        return HttpResponse(json.dumps({'result': result}), content_type='application/json')

    def invitation_add(self):
        """
        Invites a user to contribute in a problem. Will let objects created for
        Invitation and User, giving access to the user on RegistrationView.
        """
        # Validation
        problem = get_object_or_404(models.Problem, id=self.request.GET['problem'])
        if not permissions.problem(obj=problem, user=self.request.user, mode='manage'):
            raise PermissionDenied
        if 'contributor_add' not in self.request.GET \
            or not is_email(self.request.GET['contributor_add']):
            raise PermissionDenied

        # Commit
        # user
        email = self.request.GET['contributor_add']
        user = get_object_or_none(User, email=email)
        if not user:
            user = User.objects.create(username=email, email=email, first_name=email,
                is_active=False, is_staff=False)
        problem.contributor.add(user)
        # invitation
        hash = '%032x' % random.getrandbits(128)
        while models.Invitation.objects.filter(hash=hash).exists():
            hash = '%032x' % random.getrandbits(128)
        invitation = models.Invitation.objects.create(user=user, hash=hash)
        # notification
        notification.send([user], 'invitation', email_context({ 'invitation': invitation }))

        # Response
        result = loader.render_to_string('_update_problem_users.html', {'users': problem.contributor.order_by('first_name')})
        return HttpResponse(json.dumps({'result':result}))

    def activity_reset_counter(self):
        """
        Reset the activity counter.
        """
        # Validation
        if not self.request.user.is_authenticated():
            raise Http404

        # Commit
        _activity_reset_counter(self.request.user)

        # Response
        return HttpResponse(json.dumps({'ok': 1}), content_type='application/json')

    def criteria_submit(self):
        """
        Submit a criteria for a problem on ProblemUpdateView.
        """
        # Permissions check
        problem = get_object_or_404(models.Problem, id=self.request.POST.get('problem_id'))
        if not permissions.problem(obj=problem, user=self.request.user, mode='manage'):
            raise PermissionDenied

        # Commit
        # set data
        obj = get_object_or_none(models.Criteria, id=self.request.POST.get('id', None))
        self.request.POST = self.request.POST.copy()
        self.request.POST['author'] = self.request.user.id
        self.request.POST['description'] = self.request.POST['criteria_description']
        criteria = CriteriaForm(self.request.POST)
        criteria.instance = obj if obj else criteria.instance
        criteria.instance.problem = problem
        # save
        if not criteria.is_valid():
            return HttpResponse(json.dumps({'errors':dict(criteria.errors)}), content_type='application/json')
        criteria.save()
        # reload with updated data
        criteria = CriteriaForm(instance=criteria.instance)
        criteria.instance.fill_data()

        # Response
        activity_register(self.request.user, criteria.instance)
        result = loader.render_to_string('item_criteria.html', {'criteria': criteria.instance, 'show_actions': True, 'criteria_form': criteria})
        return HttpResponse(json.dumps({'result': result}), content_type='application/json')

    def new_alternative(self):
        """
        Create a new alternative.
        """
        # Validation
        problem = get_object_or_404(models.Problem, id=self.request.GET['problem'])
        if not problem or not self.request.user.is_authenticated():
            raise Http404
        if not permissions.problem(obj=problem, user=self.request.user, mode='manage'):
            raise PermissionDenied

        # Commit
        order = models.Alternative.objects.filter(problem=problem).count() + 1
        a = models.Alternative(problem=problem, order=order)
        a.save()
        a.fill_data()

        # Response
        activity_register(self.request.user, a)
        response = {
            'id': a.id,
            'html': loader.render_to_string('item_alternative.html', {
                'alternative': a,
                'problem_perm_manage': True
            })
        }
        return HttpResponse(json.dumps(response), content_type='application/json')

    def comment_new(self):
        """
        Comment on a problem, criteria, idea or alternative.
        """
        # Validation
        # comment
        content = self.request.POST.get('content', None)
        if not content:
            raise Http404
        comment = models.Comment(content=content, author=self.request.user)
        # problem
        problem = self.request.POST.get('problem', None)
        if problem:
            _obj = get_object_or_none(models.Problem, id=problem)
            comment.problem = _obj
            _problem = _obj
            target = '#comments-problem-%d' % _obj.id
        # criteria
        criteria = self.request.POST.get('criteria', None)
        if criteria:
            _obj = get_object_or_none(models.Criteria, id=criteria)
            comment.criteria = _obj
            _problem = _obj.problem
            target = '#comments-criteria-%d' % _obj.id
        # idea
        idea = self.request.POST.get('idea', None)
        if idea:
            _obj = get_object_or_none(models.Idea, id=idea)
            comment.idea = _obj
            _problem = _obj.problem
            target = '#comments-idea-%d' % _obj.id
        # alternative
        alternative = self.request.POST.get('alternative', None)
        if alternative:
            _obj = get_object_or_none(models.Alternative, id=alternative)
            comment.alternative = _obj
            _problem = _obj.problem
            target = '#comments-alternative-%d' % _obj.id
        # permissions
        if not problem and not idea and not criteria and not alternative:
            raise Http404
        if not permissions.problem(obj=_problem, user=self.request.user, mode='contribute'):
            raise PermissionDenied

        # Commit
        comment.save()
        comment.perm_edit = permissions.problem(obj=_problem, user=self.request.user, mode='manage')

        # Response
        activity_register(self.request.user, comment)
        t = loader.get_template('item_comment.html')
        c = Context({'comment': comment})
        return HttpResponse(json.dumps({'target': target, 'html': re.sub("\n", '', t.render(c))}), content_type='application/json')

    def delete_criteria(self):
        """
        Delete criteria from the problem form.
        """
        # Validation
        c = get_object_or_404(models.Criteria, id=self.request.GET.get('delete_criteria'))
        if not c or not self.request.user.is_authenticated() or 'on' != self.request.GET.get('yes', None):
            raise Http404
        if not permissions.problem(obj=c.problem, user=self.request.user, mode='manage'):
            raise PermissionDenied

        # Commit
        deleted_id = c.id
        c.delete()

        # Response
        return HttpResponse(json.dumps({ 'deleted': deleted_id }), content_type='application/json')

    def delete_alternative(self):
        """
        Delete alternative.
        """
        # Validation
        a = get_object_or_404(models.Alternative, id=self.request.GET.get('delete_alternative'))
        if not a or not self.request.user.is_authenticated():
            raise Http404
        if not permissions.problem(obj=a.problem, user=self.request.user, mode='manage'):
            raise PermissionDenied

        # Commit
        deleted_id = a.id
        problem = a.problem
        a.delete()
        i = 0
        # reorder the remaining alternatives
        for a in models.Alternative.objects.filter(problem=problem).order_by('order'):
            i += 1
            a.order = i
            a.save()

        # Response
        return HttpResponse(json.dumps({'deleted': deleted_id}), content_type='application/json')

    def vote_alternative(self):
        """
        Vote for an alternative.
        """
        # Validation
        a = get_object_or_404(models.Alternative, id=self.request.GET.get('vote_alternative'))
        if not a or not self.request.user.is_authenticated():
            raise Http404

        # Commit
        vote = models.Vote.objects.filter(alternative=a, author=self.request.user)
        if len(vote) > 0:
            vote.delete()
            voted = False
        else:
            models.Vote(alternative=a, author=self.request.user).save()
            voted = True

        # Response
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

        # Commit
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
        response = {'html': loader.render_to_string('item_alternative.html', {
            'alternative': alternative,
            'problem_perm_manage': True})}
        return HttpResponse(json.dumps(response), content_type='application/json')

    def idea_like(self):
        """
        Performs a 'like' and 'unlike' action on an idea.
        """
        # Validation
        idea = get_object_or_404(models.Idea, id=self.request.GET.get('idea_like', None))
        if not permissions.idea(obj=idea, user=self.request.user, mode='contribute'):
            return HttpResponseForbidden()

        # Commit
        if models.Vote.objects.filter(idea=idea, author=self.request.user).exists():
            models.Vote.objects.filter(idea=idea, author=self.request.user).delete()
            voted = False
        else:
            models.Vote.objects.create(idea=idea, author=self.request.user)
            voted = True

        # Response
        response = {'counter': idea.vote_count(), 'voted': voted}
        return HttpResponse(json.dumps(response), content_type='application/json')

    def alternative_like(self):
        """
        Performs a 'like' and 'unlike' action on an alternative.
        """
        # Validation
        alternative = get_object_or_404(models.Alternative, id=self.request.GET.get('alternative_like', None))
        if not permissions.problem(obj=alternative.problem, user=self.request.user, mode='contribute'):
            return HttpResponseForbidden()

        # Commit
        if models.Vote.objects.filter(alternative=alternative, author=self.request.user).exists():
            models.Vote.objects.filter(alternative=alternative, author=self.request.user).delete()
            voted = False
        else:
            models.Vote.objects.create(alternative=alternative, author=self.request.user)
            voted = True

        # Response
        response = {'counter': alternative.vote_count(), 'voted': voted}
        return HttpResponse(json.dumps(response), content_type='application/json')

