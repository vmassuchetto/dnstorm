from django import template

register = template.Library()

def get_display_name(user):
    return user.username if user.first_name == '' else user.first_name

def display_name(user):
    return get_display_name(user)

register.simple_tag(display_name)
register.assignment_tag(get_display_name)
