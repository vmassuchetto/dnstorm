from django import template

register = template.Library()

@register.filter
def is_problem_admin(user, problem):
    if user in problem.admin:
        return True
    return False
