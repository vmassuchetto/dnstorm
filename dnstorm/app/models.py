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

from actstream import registry
from autoslug import AutoSlugField
from ckeditor.fields import RichTextField
from registration.signals import user_activated

from dnstorm import settings
from dnstorm.app import permissions

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
            'site_description': _('An idea-generation platform')
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

class Criteria(models.Model):
    """
    When creating a problem, managers should define some criterias as a
    reference for the ideas submitted by users. These will also be the columns
    for the strategy table of the problem.

    Attributes:
        * ``help_star[1-5]`` Help message to explain the meaning of each star
          for the given criteria.
    """

    name = models.CharField(verbose_name=_('Name'), max_length=90, blank=False)
    slug = AutoSlugField(populate_from='name', max_length=60, editable=False, unique=True)
    description = models.TextField(verbose_name=_('Description for the criteria'), blank=False)
    help_star1 = models.CharField(verbose_name=_('Description for 1 star'), max_length=255, blank=False)
    help_star2 = models.CharField(verbose_name=_('Description for 2 stars'), max_length=255, blank=False)
    help_star3 = models.CharField(verbose_name=_('Description for 3 stars'), max_length=255, blank=False)
    help_star4 = models.CharField(verbose_name=_('Description for 4 stars'), max_length=255, blank=False)
    help_star5 = models.CharField(verbose_name=_('Description for 5 stars'), max_length=255, blank=False)
    author = models.ForeignKey(User, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False, default='2001-01-01')
    updated = models.DateTimeField(auto_now=True, editable=False, default='2001-01-01')

    def __init__(self, *args, **kwargs):
        """
        Insert extra data to ease the template rendering.
        """
        super(Criteria, self).__init__(*args, **kwargs)
        self.helps = list()
        for i in range(1,6):
            self.helps.append({
                'stars': mark_safe(''.join(['<i class="fi-star"></i>' for s in range(0,i)])),
                'description': getattr(self, 'help_star%d' % i)
            })

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_criteria'

    def type(self):
        return _('criteria')

    def get_absolute_url(self, *args, **kwargs):
        return reverse('criteria_update', kwargs={'slug': self.slug })

    def problem_count(self):
        return Problem.objects.filter(criteria=self).count()

    def get_button(self):
        return mark_safe(render_to_string('criteria_button.html', {'criteria': self}))


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
    slug = AutoSlugField(populate_from='title', max_length=60, editable=False, unique=True)
    description = RichTextField(verbose_name=_('Description'))
    criteria = models.ManyToManyField(Criteria, verbose_name=_('Criterias'), editable=False)
    author = models.ForeignKey(User, related_name='author', editable=False)
    coauthor = models.ManyToManyField(User, related_name='problem_coauthor', editable=False, blank=True, null=True)
    contributor = models.ManyToManyField(User, related_name='contributor', verbose_name=_('Contributors'), blank=True, null=True)
    public = models.BooleanField(verbose_name=_('Public'), help_text=_('Anyone is able to view and contribute to this problem. If not public, you\'ll need to set the contributors on the problem page.'), default=True, blank=True)
    open = models.BooleanField(verbose_name=_('Open edit'), help_text=_('Let users change the title and description of problems and ideas as coauthors.'), default=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False, default='2000-01-01')
    updated = models.DateTimeField(auto_now=True, editable=False, default='2000-01-01')
    last_activity = models.DateTimeField(auto_now=True, editable=False, default='2000-01-01')

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_problem'

    def type(self):
        return _('problem')

    def get_absolute_url(self, *args, **kwargs):
        return reverse('problem', args=[self.slug])

    def idea_count(self):
        return Idea.objects.filter(problem=self).count()

    def alternative_count(self):
        return Alternative.objects.filter(problem=self).count()

class Invitation(models.Model):
    """
    Invitations are used to add non-registered users as collaborators of
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

class Idea(models.Model):
    """
    Ideas are the second main entity in the platform, as the
    problem-solving process requires idea generation and participation of
    users. These will after compose the strategy table.
    """

    problem = models.ForeignKey(Problem, editable=False)
    title = models.CharField(verbose_name=_('title'), max_length=90)
    content = RichTextField(config_name='idea_content')
    author = models.ForeignKey(User, editable=False)
    coauthor = models.ManyToManyField(User, related_name='idea_coauthor', editable=False, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, editable=False, default='2000-01-01')
    updated = models.DateTimeField(auto_now=True, editable=False, default='2000-01-01')

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_idea'

    def type(self):
        return _('idea')

    def get_absolute_url(self, *args, **kwargs):
        return reverse('idea', kwargs={'slug': self.problem.slug, 'pk': self.id})

    def vote_count(self):
        w = Vote.objects.filter(idea=self).count()
        return w if w else 0

    def fill_data(self, user=False):
        """
        Fill the idea with problem and user-specific data.
        """

        self.perm_manage = permissions.idea(obj=self, user=user, mode='manage')
        self.comments = Comment.objects.filter(idea=self).order_by('created')

        # Coauthor

        coauthor = self.coauthor.count()
        self.coauthor_ = self.coauthor.all()[coauthor-1] if coauthor > 0 else None

        # Criterias

        self.criterias = list()
        for criteria in self.problem.criteria.all():
            try:
                ic = IdeaCriteria.objects.get(criteria=criteria.id, idea=self.id)
            except IdeaCriteria.DoesNotExist:
                continue
            criteria.stars = xrange(ic.stars)
            criteria.stars_number = ic.stars
            self.criterias.append(criteria)

        # Comments

        for comment in self.comments:
            comment.perm_manage = permissions.comment(obj=self.problem, user=user, mode='manage')

        # Votes

        self.votes = self.vote_count()
        self.voted = Vote.objects.filter(idea=self, author=user).exists() if user and user.is_authenticated() else False

class IdeaCriteria(models.Model):
    """
    Relation between ideas and criterias. When users submit ideas they need
    to specify how the idea is supposed to be related to each of the criterias
    of the problem.

    Attributes:
        * ``stars`` 1 to 5 number that should be given by the idea author
          following the ``Criteria.help_star[1-5]`` texts.
    """

    idea = models.ForeignKey(Idea, editable=False)
    criteria = models.ForeignKey(Criteria, editable=False)
    stars = models.PositiveSmallIntegerField(editable=False, default=0)

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_idea_criteria'

    def type(self):
        return _('idea criteria')

    def get_absolute_url(self, *args, **kwargs):
        return reverse('ideacriteria', kwargs={'slug': self.problem.slug, 'pk': self.id})

class Comment(models.Model):
    """
    Comments that can be made for ideas or problems.
    """

    problem = models.ForeignKey(Problem, editable=False, blank=True, null=True)
    idea = models.ForeignKey(Idea, editable=False, blank=True, null=True)
    content = models.TextField(verbose_name=_('Comment'))
    author = models.ForeignKey(User, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False, default='2000-01-01')
    updated = models.DateTimeField(auto_now=True, editable=False, default='2000-01-01')

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_comment'

    def type(self):
        return _('comment')

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

        self.total_ideas = self.idea.all().count()
        self.votes = self.vote_count()
        self.voted = Vote.objects.filter(alternative=self, author=user).exists() if isinstance(user, User) else False
        self.total_ratio = 0
        self.criteria = list()
        for c in self.problem.criteria.all():
            c.total_stars = IdeaCriteria.objects.filter(idea__in=self.idea.all(), criteria=c).aggregate(stars=Sum('stars'))['stars']
            c.total_stars = c.total_stars if c.total_stars else 0
            c.star_ratio = c.total_stars * 100 / self.total_ideas / 5 if c.total_stars > 0 and self.total_ideas > 0 else 0
            self.total_ratio += c.star_ratio
            self.criteria.append(c)
        self.total_ratio = self.total_ratio / len(self.criteria) if self.criteria else 0

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
