from django.db.models import Q
from django.contrib.auth.models import AnonymousUser

def problem(**kwargs):
    obj = kwargs.get('obj')
    user = kwargs.get('user')
    mode = kwargs.get('mode', 'view')
    if not obj:
        return False
    if user and user.is_superuser:
        return True
    if mode == 'view':
        return obj.public == True or obj.author == user \
            or user in obj.contributor.all() or user in obj.manager.all()
    elif mode == 'manage':
        return obj.author == user or user in obj.manager.all()
    elif mode == 'contribute':
        return obj.author == user or user in obj.manager.all() or user in obj.contributor.all()
    return False

def problem_queryset(**kwargs):
    user = kwargs.get('user', None)
    if not user:
        return Q(public=True)
    if user.is_superuser:
        return Q()
    return Q(author=user.id) | Q(contributor__in=[user.id]) | Q(manager__in=[user.id]) | Q(public=True)

def idea(**kwargs):
    obj = kwargs.get('obj')
    user = kwargs.get('user')
    mode = kwargs.get('mode', 'edit')
    if not obj:
        return False
    if user and user.is_superuser:
        return True
    if mode == 'edit':
        return obj.author == user or user in obj.problem.manager.all()
    elif mode == 'delete':
        return obj.author == user or user in obj.problem.manager.all()
    elif mode == 'undelete':
        return (obj.deleted_by) and (user == obj.deleted_by or user in obj.problem.manager.all())
    return False

def idea_queryset(**kwargs):
    user = kwargs.get('user', None)
    if user and user.is_superuser:
        return Q()
    return (Q(author=user.id) | Q(problem__manager__in=[user.id]) | Q(deleted_by__isnull=True))

def comment(**kwargs):
    obj = kwargs.get('obj')
    user = kwargs.get('user')
    mode = kwargs.get('mode', 'edit')
    if not obj:
        return False
    if user and user.is_superuser:
        return True
    if mode == 'edit':
        return obj.author == user or user in obj.problem.manager.all()
    return False
