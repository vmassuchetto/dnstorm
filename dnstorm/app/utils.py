from actstream.models import followers

from dnstorm.app import DNSTORM_URL
from dnstorm.app.models import Option

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
    Wrapper for ``get_option`` method. Tribute to WordPress.
    """

    return Option().get(name)

def update_option(name, value):
    """
    Wrapper for ``update_option`` method. Tribute to WordPress.
    """

    return Option().update(name, value)

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
