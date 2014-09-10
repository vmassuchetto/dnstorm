DNSTORM_VERSION = '0.01'
DNSTORM_URL = 'http://vmassuchetto.github.io/dnstorm'

import signals

# Activity stream

from django.contrib.auth.models import User
from actstream import registry
from dnstorm.app import models

registry.register(User)
registry.register(models.Problem)
registry.register(models.Idea)
registry.register(models.Comment)
