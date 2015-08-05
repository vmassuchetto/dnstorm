import operator
import random
import re
from datetime import datetime
from collections import OrderedDict

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Avg
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from autoslug import AutoSlugField
from ckeditor.fields import RichTextField
from registration.signals import user_activated

from dnstorm import settings
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

    Permissions flags are the following:
     * published: if the problem is published or in draft mode
     * open: open contribution mode -- anyone will be able to edit objects
     * public: if the problem can be viewed by non-collaborators

    Attributes:
     * ``last_activity`` Gets updated in favor of the ``ActivityManager``
       ordering every time an idea or a comment is made for this problem.
    """
    title = models.CharField(verbose_name=_('Title'), max_length=90, help_text=_('Give your problem a compreensive title, this will be the main call for users.'))
    slug = AutoSlugField(populate_from='title', max_length=60, editable=False, unique=True, always_update=True)
    description = RichTextField(verbose_name=_('Description'), help_text=_('The description needs to be complete and address all the variables of the problem, giving users the correct parameters to give ideas according to the criteria specified.'))
    author = models.ForeignKey(User, related_name='author', editable=False)
    coauthor = models.ManyToManyField(User, related_name='coauthor', editable=False, blank=True, null=True)
    collaborator = models.ManyToManyField(User, related_name='collaborator', verbose_name=_('Collaborators'), blank=True, null=True)
    published = models.BooleanField(default=True, blank=True)
    open = models.BooleanField(default=True, blank=True)
    public = models.BooleanField(default=True, blank=True)
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
        return self.idea_set.filter(published=True).count()

    def alternative_count(self):
        return self.alternative_set.count()

    def criteria_count(self):
        return self.criteria_set.count()

    def get_data(self, user=False):
        if not hasattr(self, '_data'):
            self.fill_data(user)
        self._data = True

    def fill_data(self, user=False):
        self.criteria_results = list()
        self.comments = Comment.objects.filter(problem=self).order_by('created')
        for c in self.criteria_set.all().order_by('name'):
            alternatives = list()
            for a in self.alternative_set.all():
                a.get_data(user)
                a.value = a.results[c.id].result_value
                alternatives.append(a)
            alternatives.sort(key=lambda x:x.name, reverse=True)
            self.criteria_results.append({'criteria': c, 'alternatives': alternatives})

    def send_invitation(self, request):
        invitation = get_object_or_none(models.Invitation, user=self)
        label = '<span class="label radius alert">%s</span>' % self.last_name
        if invitation:
            notification.send([self], 'invitation', email_context({ 'invitation': invitation }))
            messages.success(self.request, mark_safe(_('The invitation to %s was sent.') % label))
        else:
            messages.warning(self.request, mark_safe(_('Wront request information for %s.') % label))

class Criteria(models.Model):
    """
    When creating a problem, managers should define some criterias as a
    reference for the ideas submitted by users. These will also be the columns
    for the strategy table of the problem.
    """
    problem = models.ForeignKey(Problem, blank=False, null=False, editable=False)
    name = models.CharField(verbose_name=_('Name'), max_length=90, blank=False)
    slug = AutoSlugField(populate_from='name', max_length=60, editable=False, unique=True, always_update=True)
    description = models.TextField(verbose_name=_('Description for the criteria'), blank=False, help_text=_('This description should give users the information needed to fill the required values in ideas. Try to be specific about the needs and limits.'))
    fmt = models.CharField(verbose_name=('Format'), max_length=10,
        help_text=_('What format of data will be used to quantify the ideas.'),
        default='number', choices=(
            ('number', _('Number')),
            ('currency', _('Currency')),
            ('scale', _('Scale')),
            ('time', _('Time')),
            ('boolean', _('Yes or no'))))
    min = models.IntegerField(verbose_name=_('Minimum scale value'), blank=True, null=True, help_text=_('Minimum value for the ideas.'))
    max = models.IntegerField(verbose_name=_('Maximum scale value'), blank=True, null=True, help_text=_('Maximum value for the ideas.'))
    order = models.CharField(verbose_name=_('Comparison order'), max_length=4, choices=(
        ('asc', _('The higher, the better.')),
        ('desc', _('The lower, the better.'))
    ), help_text=_('Ordering that will be respected to present the results about this criteria.'))
    weight = models.PositiveIntegerField(verbose_name=_('Weight'), blank=True, null=True, help_text=_('How important this criteria is over the rest. This value will multiply over the results when presenting the alterantives.'))
    result = models.CharField(verbose_name=_('Result presenting mode'), max_length=10, choices=(
        ('sum', _('Sum')),
        ('average', _('Average')),
        ('absolute', _('Absolute')),
    ), help_text=_('How the results will be calculated across the given ideas.'))
    author = models.ForeignKey(User, blank=False, null=False)
    coauthor = models.ManyToManyField(User, related_name='criteria_coauthor', editable=False, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, default='2000-01-01')
    updated = models.DateTimeField(auto_now=True, default='2000-01-01')

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_criteria'

    def type(self):
        return _('criteria')

    def get_absolute_url(self, *args, **kwargs):
        return reverse('problem_criterion', kwargs={
            'pk': self.problem.id,
            'slug': self.problem.slug,
            'criteria': self.id })

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

    def tooltip(self):
        return re.sub('\n', '', re.sub(' {2,}', '',
            render_to_string('item_criteria_parameters.html',
            {'criteria': self, 'show_paragraphs': True, 'show_icons': True})))

    def get_data(self, user=False):
        if not hasattr(self, '_data'):
            self.fill_data(user)
        self._data = True

    def fill_data(self, user=False):
        self.comments = Comment.objects.filter(criteria=self).order_by('created')

class Idea(models.Model):
    """
    Ideas are the second main entity in the platform, as the
    problem-solving process requires idea generation and participation of
    users. These will after compose the strategy table.
    """
    problem = models.ForeignKey(Problem, editable=False)
    title = models.CharField(verbose_name=_('title'), max_length=90, help_text=_('Describe in a general basis what is the idea you\'re given to address the problem.'))
    description = RichTextField(verbose_name=_('Description'), config_name='idea')
    author = models.ForeignKey(User, editable=False)
    coauthor = models.ManyToManyField(User, related_name='idea_coauthor', editable=False, blank=True, null=True)
    published = models.BooleanField(editable=False, blank=True, default=False)
    created = models.DateTimeField(auto_now_add=True, default='2000-01-01')
    updated = models.DateTimeField(auto_now=True, default='2000-01-01')

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_idea'

    def type(self):
        return _('idea')

    def get_absolute_url(self, *args, **kwargs):
        return reverse('problem_idea', kwargs={
            'pk': self.problem.id,
            'slug': self.problem.slug,
            'idea': self.id })

    def vote_count(self):
        w = Vote.objects.filter(idea=self).count()
        return w if w else 0

    def tooltip(self):
        self.get_data()
        html = []
        for c in self.criteria:
            html.append(render_to_string('item_idea_tooltip.html', {
                'criteria': c, 'show_paragraphs': True,
                'show_icons': True, 'mode': 'tooltip'}))
        return re.sub('\n', '', re.sub(' {2,}', '', ''.join(html)))

    def get_data(self, user=False):
        if not hasattr(self, '_data'):
            self.fill_data(user)
        self._data = True

    def fill_data(self, user=False):
        """
        Fill the idea with problem and user-specific data.
        """
        self.comments = Comment.objects.filter(idea=self).order_by('created')

        # Criterias

        self.criteria = list()
        for c in self.problem.criteria_set.all():
            ic = get_object_or_none(IdeaCriteria, idea=self, criteria=c)
            c.value = ic.get_value() if ic else ''
            d = getattr(ic, 'description', '')
            c.user_description = d
            c.get_data()
            self.criteria.append(c)

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
        if self.criteria.fmt in ['number', 'scale', 'time', 'integer', 'boolean']:
            try:
                v = int(getattr(self, 'value_%s' % self.criteria.fmt))
            except:
                v = 0
        elif self.criteria.fmt in ['currency']:
            v = getattr(self, 'value_%s' % self.criteria.fmt)
        return v

class Alternative(models.Model):
    """
    Alternatives are the strategy table rows where ideas can be allocated.
    """
    name = models.CharField(max_length=255)
    problem = models.ForeignKey(Problem, editable=False)
    idea = models.ManyToManyField(Idea, editable=False, null=True, blank=True)
    author = models.ForeignKey(User, editable=False)
    coauthor = models.ManyToManyField(User, related_name='alternative_coauthor', editable=False, blank=True, null=True)
    order = models.PositiveSmallIntegerField(editable=False, default=0)
    created = models.DateTimeField(auto_now_add=True, editable=False, default='2001-01-01')
    updated = models.DateTimeField(auto_now=True, editable=False, default='2000-01-01')

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_alternative'

    def type(self):
        return _('alternative')

    def get_absolute_url(self, *args, **kwargs):
        return reverse('problem_alternative', kwargs={
            'pk': self.problem.id,
            'slug': self.problem.slug,
            'alternative': self.id })

    def vote_count(self):
        w = Vote.objects.filter(alternative=self).count()
        return w if w else 0

    def get_data(self, user=False):
        if not hasattr(self, '_data'):
            self.fill_data(user)
        self._data = True

    def fill_data(self, user=False):
        """
        Fill the alternative with problem and user-specific data.
        """
        self.comments = Comment.objects.filter(alternative=self).order_by('created')
        self.total_ideas = self.idea.all().count()
        # Votes
        self.votes = self.vote_count()
        if user and user.is_authenticated():
            vote = get_object_or_none(Vote, alternative=self, author=user)
        else:
            vote = False
        self.voted = True if vote else False
        self.vote_value = vote.value if vote else 0
        self.vote_average = Vote.objects.filter(alternative=self).aggregate(avg=Avg('value'))['avg']
        self.vote_average = '%2.d%%' % self.vote_average if self.vote_average else '0%'
        self.vote_objects = Vote.objects.filter(alternative=self).order_by('-value')
        # Criteria
        self.results = dict()
        for c in self.problem.criteria_set.order_by('name').all():
            c.get_data()
            self.fmt = c.fmt
            c.ideas = list()
            c.result_value = 0
            self.results[c.id] = c
            if self.idea.count() == 0:
                continue
            for i in self.idea.all():
                ic = get_object_or_none(IdeaCriteria, idea=i, criteria=c)
                i.value = ic.get_value() if ic else 0
                c.ideas.append(i)
                weight = getattr(c, 'weight')
                weight = weight if weight else 1
                self.results[c.id].criteria_name = c.name

                # Just sum for sums or averages
                if c.result == 'sum' or c.result == 'average':
                    self.results[c.id].result_value += i.value * weight

                # Absolute results depend on value ordering
                elif c.result == 'absolute' and c.order == 'asc':
                    self.results[c.id].result_value = i.value \
                        if i.value > self.results[c.id].result_value \
                        else self.results[c.id].result_value
                elif c.result == 'absolute' and c.order == 'desc':
                    self.results[c.id].result_value = i.value \
                        if i.value < self.results[c.id].result_value \
                        else self.results[c.id].result_value

            # Finish the average
            if c.result == 'average':
                self.results[c.id].result_value = self.results[c.id].result_value / self.idea.count()

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
    value = models.IntegerField(blank=True, null=True, default=0)
    author = models.ForeignKey(User)
    created = models.DateTimeField(auto_now_add=True, editable=False, default='2001-01-01')

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_vote'

    def type(self):
        return _('vote')

class Invitation(models.Model):
    """
    Invitations are used to add non-registered users as contributors of
    problems. The user will have access granted to the problem on registration.
    """
    user = models.ForeignKey(User)
    hash = models.CharField(max_length=128)

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_invitation'

    def type(self):
        return _('invitation')

    def get_absolute_url(self):
        return 'http://%s%s?hash=%s' % (Site.objects.get_current(), reverse('registration_register'), self.hash)
