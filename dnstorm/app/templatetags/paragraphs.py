from django.template import Library, Node
from django.template.defaultfilters import stringfilter
import re

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
