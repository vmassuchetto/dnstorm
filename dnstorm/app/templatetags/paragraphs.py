import re

from django.template import Library
from django.template.defaultfilters import stringfilter

register = Library()

def paragraphs(value):
    """
    Turns paragraphs delineated with newline characters into
    paragraphs wrapped in <p> and </p> HTML tags.
    """
    paras = re.split(r'[\r\n]+', value)
    paras = ['<p>%s</p>' % p.strip() for p in paras]
    return '\n'.join(paras)

paragraphs = stringfilter(paragraphs)
register.filter(paragraphs)
