import re

from django.template import Library
from django.template.defaultfilters import stringfilter

register = Library()

TAG_RE = re.compile(r'<[^>]+>')

def remove_tags(value):
    """
    Removes all HTML tags from text.
    """
    TAG_RE = re.compile(r'<[^>]+>')
    return TAG_RE.sub('', value)

remove_tags = stringfilter(remove_tags)
register.filter(remove_tags)
