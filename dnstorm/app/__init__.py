import signals
from django.contrib.auth.models import User
from actstream import registry
from dnstorm.app import models

DNSTORM_VERSION = '0.01'
DNSTORM_URL = 'http://vmassuchetto.github.io/dnstorm'

registry.register(User)
registry.register(models.Problem)
registry.register(models.Criteria)
registry.register(models.Idea)
registry.register(models.Alternative)
registry.register(models.Comment)
