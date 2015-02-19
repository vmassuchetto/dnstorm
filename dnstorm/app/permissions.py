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
        return (
            (not obj.published and obj.author == user)
            or (
                (obj.published and obj.public)
                or obj.author == user
                or user in obj.contributor.all()
            )
        )
    elif mode == 'contribute':
        return (
            (obj.published and user.is_authenticated())
            and (
                obj.public
                or obj.author == user
                or user in obj.contributor.all()
            )
        )
    elif mode == 'edit':
        return (
            (user.is_authenticated())
            and (
                (obj.public and obj.open)
                or (obj.open and user in obj.contributor.all())
                or obj.author == user
            )
        )
    elif mode == 'manage':
        return (
            (user and user.is_authenticated())
            and obj.author == user
        )
    return False

def problem_queryset(**kwargs):
    """
    Return a queryset to get allowed problems.
    """
    user = kwargs.get('user')
    return ((
            (Q(published=True) & Q(public=True))
            | (Q(published=False) & Q(author=user.id))
        ) | (
            (Q(published=True))
            & (Q(author=user.id) | Q(contributor=user.id))
        ))

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
        return (user and obj.author == user) or problem(obj=obj.problem, user=user, mode='manage')
    elif mode == 'edit':
        return problem(obj=obj.problem, user=user, mode='edit')
    return False

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

def criteria(**kwargs):
    """
    Regulate permissions for criteria objects.
    """
    obj = kwargs.get('obj')
    user = kwargs.get('user')
    mode = kwargs.get('mode', 'manage')
    if not obj:
        return False
    if user and user.is_superuser:
        return True
    elif mode == 'manage':
        return obj.author == user
    return False

def user(**kwargs):
    """
    Regulate permissions for user objects.
    """
    obj = kwargs.get('obj')
    user = kwargs.get('user')
    mode = kwargs.get('mode', 'manage')
    if not obj or not user or not mode:
        return False
    return (user and user.is_superuser) or (user.id == obj.id)
