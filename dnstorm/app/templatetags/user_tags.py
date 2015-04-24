from django.template import Library

from dnstorm.app import models

register = Library()

def user_problem_count(user):
    return models.Problem.objects.filter(author=user, published=True).count()

def user_idea_count(user):
    return models.Idea.objects.filter(author=user, published=True).count()

def user_comment_count(user):
    return models.Comment.objects.filter(author=user).count()

register.filter(user_problem_count)
register.filter(user_idea_count)
register.filter(user_comment_count)
