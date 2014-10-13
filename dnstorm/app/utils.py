from django.contrib.auth.models import User

from actstream.models import followers

from dnstorm.app import DNSTORM_URL
from dnstorm.app.models import Option, Problem, Idea, Comment

def get_object_or_none(klass, *args, **kwargs):
    """
    Get an object and return None if not found.
    """

    try:
        return klass._default_manager.get(*args, **kwargs)
    except klass.DoesNotExist:
        return None

def get_option(name):
    """
    Wrapper for ``get`` method of Option class. A tribute to WordPress.
    """

    return Option().get(name)

def update_option(name, value):
    """
    Wrapper for ``update`` method of Option class. A tribute to WordPress.
    """

    return Option().update(name, value)

def get_user(username):
    """
    Return user information.
    """
    user = get_object_or_none(User, username=username, is_active=True)
    if not user:
        return None
    user.problem_count = Problem.objects.filter(author=user).count()
    user.idea_count = Idea.objects.filter(author=user).count()
    user.comment_count = Comment.objects.filter(author=user).count()
    return user

def activity_reset_counter(user):
    """
    Resets the activity stream counter for a user.
    """

    return update_option('user_%d_activity_counter' % user.id, 0)

def activity_count(obj):
    """
    Increments the activity stream counter of the followers of the given object
    to make a Facebook look and feel on the top bar.
    """

    for user in followers(obj):
        name = 'user_%d_activity_counter' % user.id
        count = get_option(name)
        try:
            count = int(count)
        except:
            count = 0
        update_option(name, count+1)

def email_context(more_context=dict()):
    """
    Puts ``more_context`` with the standard context variables required for
    sending e-mails.
    """

    return dict(dict({
        'dnstorm_url': DNSTORM_URL,
        'site_title': get_option('site_title'),
        'site_url': get_option('site_url')
    }).items() + more_context.items())
