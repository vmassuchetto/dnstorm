import re
from datetime import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db import models, connection
from django.db.models import Sum
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from autoslug import AutoSlugField
from ckeditor.fields import RichTextField
from registration.signals import user_activated

from dnstorm import settings
from dnstorm.app import permissions
from dnstorm.app.utils import get_object_or_none

class Option(models.Model):
    """
    Meta-based table to store general site options retrieved via the ``get``
    method.

    Attributes:
        * ``name`` unique entry key
        * ``value`` value for the key
    """

    name = models.TextField(verbose_name=_('Name'), blank=False, unique=True)
    value = models.TextField(verbose_name=_('Value'), blank=False)

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_option'

    def type(self):
        return _('option')

    def get(self, *args):
        """
        The site options are defined and saved by the OptionsForm fields,
        and this method ensures that some value or a default value will be
        returned when querying for an option value. `None` is returned if the
        option name is invalid.
        """

        if len(args) <= 0 or len(args) > 1:
            return None
        try:
            option = Option.objects.get(name=args[0])
            value = option.value
        except Option.DoesNotExist:
            defaults = self.get_defaults()
            if args[0] not in defaults:
                return None
            value = defaults[args[0]]
        return value

    def update(self, *args):
        """
        Update a value based on the option name.
        """
        if len(args) <= 0 or len(args) > 2:
            return None
        try:
            option = Option.objects.get(name=args[0])
        except Option.DoesNotExist:
            option = Option(name=args[0], value=None)
        option.value = args[1]
        option.save()
        return True

    def get_defaults(self, *args, **kwargs):
        """
        These are some default values that are used in templates and
        somewhere else. They are supposed to be overwritten by values on
        database.
        """
        return {
            'site_title': 'DNStorm',
            'site_description': unicode(_('An idea-generation platform'))
        }

    def get_all(self):
        """
        Get all the default values.
        """

        options = dict()
        defaults = self.get_defaults()
        for default in defaults:
            options[default] = self.get(default)
        return options

class Problem(models.Model):
    """
    Problems are the central entity of the platform, as everything goes
    around them. This is no more than the suubject of discussion for generating
    ideas and a strategy table.

    Attributes:
        * ``last_activity`` Gets updated in favor of the ``ActivityManager``
          ordering every time an idea or a comment is made for this problem.
    """

    title = models.CharField(verbose_name=_('Title'), max_length=90)
    slug = AutoSlugField(populate_from='title', max_length=60, editable=False, unique=True, always_update=True)
    description = RichTextField(verbose_name=_('Description'))
    author = models.ForeignKey(User, related_name='author', editable=False)
    coauthor = models.ManyToManyField(User, related_name='problem_coauthor', editable=False, blank=True, null=True)
    contributor = models.ManyToManyField(User, related_name='contributor', verbose_name=_('Contributors'), blank=True, null=True)
    public = models.BooleanField(verbose_name=_('Public'), help_text=_('Anyone is able to view and contribute to this problem. If not public, you\'ll need to choose the contributors that will have access to it.'), default=True, blank=True)
    open = models.BooleanField(verbose_name=_('Open edit'), help_text=_('Let users change the title and description of problems and ideas as coauthors.'), default=True, blank=True)
    published = models.BooleanField(editable=False, blank=True, default=False)
    models.CharField(verbose_name=_('Publish status'), max_length=10, editable=False, blank=False, choices=(
        ('draft', _('Draft')),
        ('published', _('Published'))
    ))
    created = models.DateTimeField(auto_now_add=True, editable=False, default='2000-01-01')
    updated = models.DateTimeField(auto_now=True, editable=False, default='2000-01-01')
    last_activity = models.DateTimeField(auto_now=True, editable=False, default='2000-01-01')

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_problem'

    def type(self):
        return _('problem')

    def get_absolute_url(self, *args, **kwargs):
        return reverse('problem', args=[self.id, self.slug])

    def idea_count(self):
        return 0
        #return self.probelma.criteria_set.idea_set.all().count()

    def alternative_count(self):
        return 0
        #return Alternative.objects.filter(problem=self).count()

    def criteria_count(self):
        return Criteria.objects.filter(problem=self).count()

class Criteria(models.Model):
    """
    When creating a problem, managers should define some criterias as a
    reference for the ideas submitted by users. These will also be the columns
    for the strategy table of the problem.
    """

    problem = models.ForeignKey(Problem, blank=False, null=False, editable=False)
    name = models.CharField(verbose_name=_('Name'), max_length=90, blank=False)
    slug = AutoSlugField(populate_from='name', max_length=60, editable=False, unique=True, always_update=True)
    description = models.TextField(verbose_name=_('Description for the criteria'), blank=False)
    fmt = models.CharField(verbose_name=('Format'), max_length=10, choices=(
        ('number', _('Number')),
        ('currency', _('Currency')),
        ('scale', _('Scale')),
        ('time', _('Time')),
        ('boolean', _('Yes or no'))
    ))
    min = models.IntegerField(verbose_name=_('Minimum scale value'), blank=True, null=True)
    max = models.IntegerField(verbose_name=_('Maximum scale value'), blank=True, null=True)
    order = models.CharField(verbose_name=_('Comparison order'), max_length=4, choices=(
        ('asc', _('The higher, the better.')),
        ('desc', _('The lower, the better.'))
    ))
    weight = models.PositiveIntegerField(verbose_name=_('Weight'), blank=True, null=True)
    result = models.CharField(verbose_name=_('Result presenting mode'), max_length=10, choices=(
        ('sum', _('Sum')),
        ('average', _('Average')),
        ('absolute', _('Absolute')),
    ))
    author = models.ForeignKey(User, blank=False, null=False)

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_criteria'

    def type(self):
        return _('criteria')

    def get_absolute_url(self, *args, **kwargs):
        return reverse('criteria_update', kwargs={'slug': self.slug })

    def problem_count(self):
        return Problem.objects.filter(criteria=self).count()

    def icon(self):
        icons = {
            'number': 'target',
            'currency': 'dollar',
            'scale': 'graph-trend',
            'time': 'clock',
            'boolean': 'checkbox'
        }
        return icons[self.fmt]

    def fill_data(self, user=False):
        self.comments = Comment.objects.filter(criteria=self)

class Idea(models.Model):
    """
    Ideas are the second main entity in the platform, as the
    problem-solving process requires idea generation and participation of
    users. These will after compose the strategy table.
    """

    problem = models.ForeignKey(Problem, editable=False)
    title = models.CharField(verbose_name=_('title'), max_length=90)
    slug = AutoSlugField(populate_from='title', max_length=60, editable=False, unique=True, always_update=True)
    author = models.ForeignKey(User, editable=False)
    published = models.BooleanField(editable=False, blank=True, default=False)
    created = models.DateTimeField(auto_now_add=True, default='2000-01-01')
    updated = models.DateTimeField(auto_now=True, default='2000-01-01')

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_idea'

    def type(self):
        return _('idea')

    def get_absolute_url(self, *args, **kwargs):
        return reverse('idea', kwargs={'pk': self.id})

    def vote_count(self):
        w = Vote.objects.filter(idea=self).count()
        return w if w else 0

    def fill_data(self, user=False):
        """
        Fill the idea with problem and user-specific data.
        """

        self.perm_manage = permissions.idea(obj=self, user=user, mode='manage')
        self.comments = Comment.objects.filter(idea=self).order_by('created')

        # Criterias

        self.criteria = list()
        for c in self.problem.criteria_set.all():
            ic = get_object_or_none(IdeaCriteria, idea=self, criteria=c)
            v = getattr(ic, 'value_%s' % c.fmt, None)
            c.value = v
            d = getattr(ic, 'description', None)
            c.description = d
            c.fill_data()
            self.criteria.append(c)

        # Comments

        for comment in self.comments:
            comment.perm_manage = permissions.comment(obj=self.problem, user=user, mode='manage')

        # Votes

        self.votes = self.vote_count()
        self.voted = Vote.objects.filter(idea=self, author=user).exists() if user and user.is_authenticated() else False

class IdeaCriteria(models.Model):
    """
    Builds the relationship between ideas and criteria for the user to enter a
    description about the judgements of each criteria of the problem.
    """
    idea = models.ForeignKey(Idea, blank=False, null=False, editable=False)
    criteria = models.ForeignKey(Criteria, blank=False, null=False, editable=False)
    description = models.TextField(blank=False, null=False, editable=False)
    value_number = models.IntegerField(default=0, blank=True, null=True)
    value_currency = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    value_scale = models.IntegerField(default=0, blank=True, null=True)
    value_time = models.IntegerField(default=0, blank=True, null=True)
    value_boolean = models.BooleanField(default=False, blank=True)

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_idea_criteria'

    def type(self):
        return _('idea_criteria')

    def get_value(self):
        return getattr(self, 'value_%s' % self.criteria.fmt)

class Invitation(models.Model):
    """
    Invitations are used to add non-registered users as contributors of
    problems. The user will have access granted to the problem when it
    subscribes.
    """

    problem = models.ForeignKey(Problem)
    email = models.EmailField()
    hash = models.CharField(max_length=128)

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_invitation'

    def type(self):
        return _('invitation')

    def get_absolute_url(self):
        return 'http://%s%s?hash=%s' % (Site.objects.get_current(), reverse('registration_register'), self.hash)

class Alternative(models.Model):
    """
    Alternatives are the strategy table rows where ideas can be allocated.
    """

    problem = models.ForeignKey(Problem, editable=False)
    idea = models.ManyToManyField(Idea, editable=False, null=True, blank=True)
    order = models.PositiveSmallIntegerField(editable=False, default=0)
    created = models.DateTimeField(auto_now_add=True, editable=False, default='2001-01-01')
    updated = models.DateTimeField(auto_now=True, editable=False, default='2000-01-01')

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_alternative'

    def type(self):
        return _('alternative')

    def vote_count(self):
        w = Vote.objects.filter(alternative=self).count()
        return w if w else 0

    def fill_data(self, user=False):
        """
        Fill the alternative with problem and user-specific data.
        """
        self.comments = list()
        for c in Comment.objects.filter(alternative=self.id):
            self.comments.append(c)
        self.get_results()
        self.total_ideas = self.idea.all().count()
        self.votes = self.vote_count()
        self.voted = Vote.objects.filter(alternative=self, author=user).exists() if isinstance(user, User) else False
        self.total_ratio = 0

    def get_results(self):
        self.results = dict()
        for c in self.problem.criteria_set.all():
            c.fill_data()
            self.results[c.id] = { 'criteria': c, 'value': 0 }
            if self.idea.count() == 0:
                continue
            for i in self.idea.all():
                ic = get_object_or_none(IdeaCriteria, idea=i, criteria=c)
                value = ic.get_value() if ic else 0

                # Just sum for sums or averages
                if c.result == 'sum' or c.result == 'average':
                    self.results[c.id]['value'] += value

                # Absolute results depend on value ordering
                elif c.result == 'absolute' and c.order == 'asc':
                    self.results[c.id]['value'] = value if value > self.results[c.id] else self.results[c.id]
                elif c.result == 'absolute' and c.order == 'desc':
                    self.results[c.id]['value'] = value if value < self.results[c.id] else self.results[c.id]

            # Finish the average
            if c.result == 'average':
                self.results[c.id]['value'] = '{0:.4g}'.format(self.results[c.id]['value'] / self.idea.count())

class Comment(models.Model):
    """
    Comments that can be made for ideas or problems.
    """

    problem = models.ForeignKey(Problem, editable=False, blank=True, null=True)
    idea = models.ForeignKey(Idea, editable=False, blank=True, null=True)
    criteria = models.ForeignKey(Criteria, editable=False, blank=True, null=True)
    alternative = models.ForeignKey(Alternative, editable=False, blank=True, null=True)
    content = models.TextField(verbose_name=_('Comment'))
    author = models.ForeignKey(User, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False, default='2000-01-01')
    updated = models.DateTimeField(auto_now=True, editable=False, default='2000-01-01')

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_comment'

    def type(self):
        return _('comment')

class Vote(models.Model):
    """
    Votes for ideas, comments or alternatives.
    """

    idea = models.ForeignKey(Idea, blank=True, null=True, related_name='vote_idea')
    comment = models.ForeignKey(Alternative, blank=True, null=True, related_name='vote_comment')
    alternative = models.ForeignKey(Alternative, blank=True, null=True, related_name='vote_alternative')
    author = models.ForeignKey(User)
    created = models.DateTimeField(auto_now_add=True, editable=False, default='2001-01-01')

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_vote'

    def type(self):
        return _('vote')
