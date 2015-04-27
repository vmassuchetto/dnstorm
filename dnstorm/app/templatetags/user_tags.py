import re
from django.template import Library
from dnstorm.app import models, perms

register = Library()

def user_problem_count(user):
    return models.Problem.objects.filter(author=user, published=True).count()

def user_idea_count(user):
    return models.Idea.objects.filter(author=user, published=True).count()

def user_comment_count(user):
    return models.Comment.objects.filter(author=user).count()

def problem_create(user):
    return perms.problem(user, 'create')
def problem_update(user, obj):
    return perms.problem(user, 'update', obj)
def problem_comment(user, obj):
    return perms.problem(user, 'comment', obj)
def problem_manage(user, obj):
    return perms.problem(user, 'manage', obj)
def problem_delete(user, obj):
    return perms.problem(user, 'delete', obj)
def criteria_create(user, obj):
    return perms.criteria(user, 'create', obj)
def criteria_update(user, obj):
    return perms.criteria(user, 'update', obj)
def criteria_delete(user, obj):
    return perms.criteria(user, 'delete', obj)
def idea_create(user, obj):
    return perms.idea(user, 'create', obj)
def idea_update(user, obj):
    return perms.idea(user, 'update', obj)
def idea_delete(user, obj):
    return perms.idea(user, 'delete', obj)
def alternative_create(user, obj):
    return perms.alternative(user, 'create', obj)
def alternative_update(user, obj):
    return perms.alternative(user, 'update', obj)
def alternative_delete(user, obj):
    return perms.alternative(user, 'delete', obj)

register.filter(user_problem_count)
register.filter(user_idea_count)
register.filter(user_comment_count)

register.filter(problem_create)
register.filter(problem_update)
register.filter(problem_manage)
register.filter(problem_comment)
register.filter(problem_delete)
register.filter(criteria_create)
register.filter(criteria_update)
register.filter(criteria_delete)
register.filter(idea_create)
register.filter(idea_update)
register.filter(idea_delete)
register.filter(alternative_create)
register.filter(alternative_update)
register.filter(alternative_delete)
