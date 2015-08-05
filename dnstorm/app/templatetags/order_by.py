from django.template import Library

register = Library()

@register.filter_function
def order_by(lst, args):
    args = [x.strip() for x in args.split(',')]
    return sorted(lst, key=lambda x: (getattr(x, args[0])))
