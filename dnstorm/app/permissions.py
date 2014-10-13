from django.db.models import Q
from django.contrib.auth.models import AnonymousUser

def problem(**kwargs):
    """
    Regulate permissions for problem objects.
    """

    obj = kwargs.get('obj')
    user = kwargs.get('user')
    mode = kwargs.get('mode', 'contribute')
    if not obj:
        return False
    elif user and user.is_superuser:
        return True
    elif mode == 'view':
        return obj.public or obj.author == user or user in obj.contributor.all()
    elif mode == 'contribute':
        return user.is_authenticated() and (obj.public or obj.author == user or user in obj.contributor.all())
    elif mode == 'edit':
        return user.is_authenticated() and ((obj.public and obj.open) or (obj.open and user in obj.contributor.all()) or (obj.author == user))
    elif mode == 'manage':
        return obj.author == user
    return False

def idea(**kwargs):
    """
    Regulate permissions for idea objects.
    """

    obj = kwargs.get('obj')
    user = kwargs.get('user')
    mode = kwargs.get('mode', 'manage')
    if not obj:
        return False
    elif user and user.is_superuser:
        return True
    elif mode == 'contribute':
        return problem(obj=obj.problem, user=user, mode='contribute')
    elif mode == 'manage':
        return obj.author == user or problem(obj=obj.problem, user=user, mode='manage')
    elif mode == 'edit':
        return problem(obj=obj.problem, user=user, mode='edit')
    return False

def idea_queryset(**kwargs):
    """
    Returns querysets for ideas based on user permissions.
    """

    user = kwargs.get('user', None)
    if user and user.is_superuser:
        return Q()
    return Q(author=user.id)

def comment(**kwargs):
    """
    Regulate permissions for comment objects.
    """

    obj = kwargs.get('obj')
    user = kwargs.get('user')
    mode = kwargs.get('mode', 'manage')
    if not obj:
        return False
    if user and user.is_superuser:
        return True
    if mode == 'manage' and hasattr(obj, 'problem'):
        return obj.author == user or obj.problem.author == user
    elif mode == 'manage' and hasattr(obj, 'idea'):
        return obj.author == user or obj.idea.problem.author == user
    return False
