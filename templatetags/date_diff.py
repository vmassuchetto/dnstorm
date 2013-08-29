from django import template
from django.utils.translation import ungettext, ugettext
from time import ctime
import datetime

register = template.Library()

@register.filter
def date_diff(date_param, to=None):
    if not date_param:
        return ""

    compare_with = to or datetime.date.today()
    delta = date_param.date() - compare_with

    if delta.days == 0: return u"today"
    elif delta.days == -1: return u"yesterday"
    elif delta.days == 1: return u"tomorrow"

    chunks = (
        (365.0, lambda n: ungettext('year', 'years', n)),
        (30.0, lambda n: ungettext('month', 'months', n)),
        (7.0, lambda n : ungettext('week', 'weeks', n)),
        (1.0, lambda n : ungettext('day', 'days', n)),
    )

    for i, (chunk, name) in enumerate(chunks):
        if abs(delta.days) >= chunk:
            count = abs(round(delta.days / chunk, 0))
            break

    date_str = ugettext('%(number)d %(type)s') % {'number': count, 'type': name(count)}

    if delta.days > 0: return "in " + date_str
    else: return date_str + " ago"
