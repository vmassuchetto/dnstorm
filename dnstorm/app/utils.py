
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
    from dnstorm.app.models import Option
    return Option().get(name)

def update_option(name, value):
    """
    Wrapper for ``update`` method of Option class. A tribute to WordPress.
    """
    from dnstorm.app.models import Option
    return Option().update(name, value)

def get_user(username):
    """
    Return user information.
    """
    from django.contrib.auth.models import User
    from dnstorm.app.models import Problem, Idea, Comment

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
    from actstream.models import followers

    for user in followers(obj):
        name = 'user_%d_activity_counter' % user.id
        count = get_option(name)
        try:
            count = int(count)
        except:
            count = 0
        update_option(name, count+1)

def activity_register(_user, _action_object):
    """
    Registers and activity when an object is saved.
    """
    from lxml.html.diff import htmldiff
    from actstream import action
    from actstream.actions import follow, is_following
    from actstream.models import action_object_stream
    from django.db.models.loading import get_model
    from django.forms import ValidationError
    from django.forms.models import model_to_dict
    from django.template.loader import render_to_string

    klass = _action_object.__class__.__name__.lower()
    if klass not in ['problem', 'criteria', 'idea', 'alternative', 'comment']:
        raise forms.ValidationError(_('Wrong object type'))

    # Last activity
    last = (action_object_stream(_action_object)[:1] or [None])[0]
    content_old = last.data['content'] if hasattr(last, 'data') and 'content' in last.data else ''
    _content = render_to_string(klass + '_diffbase.html', {klass: _action_object})
    _emsg = _action_object.edit_message if hasattr(_action_object, 'edit_message') else ''
    _diff = htmldiff(content_old, _content)
    _verb = 'edited'

    _obj = None
    if klass == 'comment':
        _verb = 'commented'
        _obj = _action_object
        if _action_object.problem:
            _action_object = _action_object.problem
            _target = _action_object
        elif _action_object.criteria:
            _action_object = _action_object.criteria
        elif _action_object.idea:
            _action_object = _action_object.idea
        elif _action_object.alternative:
            _action_object = _action_object.alternative
    elif not content_old:
        _verb = 'created'
    _target = _action_object.problem if hasattr(_action_object, 'problem') else _action_object

    a = action.send(_user, verb=_verb, action_object=_action_object, target=_target)
    a[0][1].data = {
        'diff': _diff,
        'content': _content,
        'edit_message': _emsg,
        'object': model_to_dict(_obj) if _obj else ''
    }
    a[0][1].save()
    activity_count(_target)
    follow(_user, _target, actor_only=False) if not is_following(_user, _target) else None

def email_context(more_context=dict()):
    """
    Puts ``more_context`` with the standard context variables required for
    sending e-mails.
    """
    from dnstorm.app import DNSTORM_URL

    return dict(dict({
        'dnstorm_url': DNSTORM_URL,
        'site_title': get_option('site_title'),
        'site_url': get_option('site_url')
    }).items() + more_context.items())
