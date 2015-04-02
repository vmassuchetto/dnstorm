from itertools import chain
from datetime import datetime

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.shortcuts import get_object_or_404

from actstream.managers import ActionManager as _ActionManager
from actstream.managers import stream

from dnstorm.app import permissions
from dnstorm.app.models import Problem, Idea, Alternative
from dnstorm.app.utils import get_object_or_none

class ActionManager(_ActionManager):

    @stream
    def global_stream(self, user, content_type):
        if content_type.name == 'problem':
            perm_qs = permissions.problem_queryset(user=user)
        elif content_type.name == 'comment':
            perm_qs = permissions.comment_queryset(user=user)
        elif content_type.name == 'idea':
            perm_qs = permissions.problem_fk_queryset(user=user)
        else:
            perm_qs = permissions.problem_fk_queryset(user=user)
        return (perm_qs, Q(action_object_content_type_id=content_type.id))

    @stream
    def problem_stream(self, user, problem):
        perm_qs = permissions.problem_queryset(user=user)
        return (Q(target_object_id=problem.id),)

    @stream
    def problem_objects_stream(self, user, problem, content_type):
        if content_type.name == 'problem':
            perm_qs = permissions.problem_queryset(user=user)
        elif content_type.name == 'comment':
            perm_qs = permissions.comment_queryset(user=user)
        elif content_type.name == 'idea':
            perm_qs = permissions.problem_fk_queryset(user=user)
        else:
            perm_qs = permissions.problem_fk_queryset(user=user)
        return (perm_qs,
            Q(action_object_content_type_id=content_type.id),
            Q(target_object_id=problem.id),)
