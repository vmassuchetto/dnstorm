from django.db.models import Q
from django.contrib.auth.models import AnonymousUser

def problem(**kwargs):
    obj = kwargs.get('obj')
    user = kwargs.get('user')
    mode = kwargs.get('mode', 'contribute')
    if not obj:
        return False
    elif user and user.is_superuser:
        return True
    elif mode == 'view':
        return obj.public or (obj.author == user or user in obj.contributor.all())
    elif mode == 'contribute':
        return user.is_authenticated() and (obj.public or (obj.author == user or user in obj.contributor.all()))
    elif mode == 'edit':
        return user.is_authenticated() and ((obj.public and obj.open) or (not obj.public and obj.open and user in obj.contributor.all()))
    elif mode == 'manage':
        return obj.author == user
    return False

def idea(**kwargs):
    obj = kwargs.get('obj')
    user = kwargs.get('user')
    mode = kwargs.get('mode', 'manage')
    if not obj:
        return False
    elif user and user.is_superuser:
        return True
    elif mode == 'manage':
        return obj.author == user or obj.problem.author == user
    elif mode == 'edit':
        return user.is_authenticated() and ((obj.problem.public and obj.problem.open) or (not obj.problem.public and obj.problem.open and user in obj.problem.contributor.all()))
    return False

def idea_queryset(**kwargs):
    user = kwargs.get('user', None)
    if user and user.is_superuser:
        return Q()
    return Q(author=user.id)

def comment(**kwargs):
    obj = kwargs.get('obj')
    user = kwargs.get('user')
    mode = kwargs.get('mode', 'manage')
    if not obj:
        return False
    if user and user.is_superuser:
        return True
    if mode == 'manage':
        return obj.author == user
    return False
