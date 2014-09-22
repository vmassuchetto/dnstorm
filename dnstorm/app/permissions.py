from django.db.models import Q
from django.contrib.auth.models import AnonymousUser

def problem(**kwargs):
    obj = kwargs.get('obj')
    user = kwargs.get('user')
    mode = kwargs.get('mode', 'contribute')
    if not obj:
        return False
    if user and user.is_superuser:
        return True
    elif mode == 'view':
        return obj.public or (obj.author == user or user in obj.contributor.all())
    elif mode == 'contribute':
        return user.is_authenticated() and (obj.public or (obj.author == user or user in obj.contributor.all()))
    elif mode == 'manage':
        return obj.author == user
    return False

def idea(**kwargs):
    obj = kwargs.get('obj')
    user = kwargs.get('user')
    mode = kwargs.get('mode', 'manage')
    if not obj:
        return False
    if user and user.is_superuser:
        return True
    if mode == 'manage':
        return obj.author == user
    elif mode == 'delete':
        return obj.author == user
    elif mode == 'undelete':
        return (obj.deleted_by) and (user == obj.deleted_by)
    return False

def idea_queryset(**kwargs):
    user = kwargs.get('user', None)
    if user and user.is_superuser:
        return Q()
    return (Q(author=user.id) | Q(deleted_by__isnull=True))

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
