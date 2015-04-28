
def problem(user, mode, obj=None):
    """
    Regulate permissions for problem objects.
    """
    if user.is_superuser:
        return True
    elif mode == 'create': # no need for obj
        return user.is_authenticated()
    elif mode == 'update':
        return (
            user.is_authenticated()
        and (
            (obj.published and obj.public and obj.open) or \
            (obj.published and obj.open and user in obj.collaborator.all()) or \
            (obj.author == user)
        ))
    elif mode == 'delete':
        return (obj.author == user)
    elif mode == 'view':
        return (
            (obj.published and obj.public) or \
            (obj.published and user in obj.collaborator.all()) or \
            (obj.author == user)
        )
    elif mode in ['comment', 'vote']:
        return (
            user.is_authenticated()
        ) and (
            (obj.published and obj.public) or \
            (obj.published and user in obj.collaborator.all()) or \
            (obj.author == user)
        )
    elif mode == 'manage':
        return obj.author == user

def criteria(user, mode, obj):
    """
    Regulate permissions for criteria objects.
    """
    if user and user.is_superuser:
        return True
    elif mode == 'create': # obj is a problem
        return (
            user.is_authenticated() \
            and obj.published
        ) and (
            (obj.open and obj.public) or \
            (obj.open and user in obj.collaborator.all()) or \
            (obj.author == user)
        )
    elif mode == 'update':
        return (
            user.is_authenticated() \
            and obj.problem.published
        ) and (
            obj.problem.public and obj.problem.open or \
            obj.problem.open and user in obj.problem.collaborator.all() or \
            obj.problem.author == user or \
            obj.author == user
        )
    elif mode == 'delete':
        return (
            obj.author == user or \
            obj.problem.author == user)

def idea(user, mode, obj):
    """
    Regulate permissions for idea objects.
    """
    if user and user.is_superuser:
        return True
    elif mode in ['create']: # obj is a problem
        return (
            user.is_authenticated() and \
            obj.published and \
            obj.criteria_set.count() > 0
        ) and (
            (obj.open) or \
            (user == obj.author) or \
            (user in obj.collaborator.all())
        )
    elif mode == 'vote':
        return (
            user.is_authenticated() and \
            obj.published and \
            user != obj.author \
        ) and (
            obj.problem.open or \
            user in obj.problem.collaborator.all()
        )
    elif mode == 'update':
        return (
            user.is_authenticated()
        ) and (
            (obj.problem.published and obj.problem.open) or \
            (user == obj.author) or \
            (user == obj.problem.author)
        )
    elif mode == 'delete':
        return (user == obj.author or \
            user == obj.problem.author)

def alternative(user, mode, obj):
    """
    Regulate permissions for alternative objects.
    """
    if user and user.is_superuser:
        return True
    elif mode == 'create': # obj is a problem
        return (
            user.is_authenticated() \
            and obj.published \
            and obj.idea_set.count() > 0
        ) and (
            (obj.open) or \
            (user == obj.author) or \
            (user in obj.collaborator.all())
        )
    elif mode == 'update':
        return (
            user.is_authenticated() \
            and obj.problem.published \
        ) and (
            (obj.problem.open and obj.problem.public) or \
            (obj.problem.open and user in obj.problem.collaborator.all()) or \
            (user == obj.author) or \
            (user == obj.problem.author)
        )
    elif mode == 'delete':
        return (user == obj.author or \
            user == obj.problem.author)
    return False
