from django.db.models import Q
from django.contrib.auth.models import AnonymousUser

def problem(**kwargs):
    """
    Regulate permissions for problem objects.
    """
    obj = kwargs.get('obj')
    user = kwargs.get('user')
    mode = kwargs.get('mode', 'view')
    if not obj:
        return False
    elif user and user.is_superuser:
        return True
    elif mode == 'view':
        return (
            (obj.published and obj.public)
            or (obj.published and user in obj.contributor.all())
            or obj.author == user
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

def problem_queryset(user, mode='view'):
    """
    Get queryset for problems.
    """
    if not user:
        return False
    elif user and user.is_superuser:
        return Q()
    elif mode == 'view':
        return (
            Q(published=True, public=True)
            | Q(published=True, contributor__in=[user])
            | Q(author=user))

def problem_fk_queryset(user, mode='view'):
    """
    Get queryset for objects where problem is a foreign key. Valid for
    Criteria, Idea and Alternative objects.
    """
    if not user:
        return False
    elif user and user.is_superuser:
        return Q()
    elif mode == 'view':
        return (
            Q(problem__published=True, problem__public=True)
            | Q(problem__published=True, problem__contributor__in=user)
            | Q(problem__author=user))

def comment_queryset(user, mode='view'):
    """
    Get queryset for comments.
    """
    if not user:
        return False
    elif user and user.is_superuser:
        return Q()
    elif mode == 'view':
        return Q((
                Q(problem__published=True, problem__public=True)
                | Q(problem__published=True, problem__contributor__in=user)
                | Q(problem__author=user)
            ) | (
                Q(idea__problem__published=True, idea__problem__public=True)
                | Q(idea__problem__published=True, idea__problem__contributor__in=user)
                | Q(idea__problem__author=user)
            ) | (
                Q(alternative__problem__published=True, alternative__problem__public=True)
                | Q(alternative__problem__published=True, alternative__problem__contributor__in=user)
                | Q(alternative__problem__author=user)
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
    return False

def alternative(**kwargs):
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
