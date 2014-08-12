import re
from datetime import datetime

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models, connection
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string
from django.db.models import Sum

import reversion
import diff_match_patch as _dmp
from dnstorm import settings
from dnstorm.app.lib.diff import diff_prettyHtml

from ckeditor.fields import RichTextField
from autoslug import AutoSlugField
from registration.signals import user_activated

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

    def get_or_create(self, **kwargs):
        if 'name' not in kwargs or 'value' not in kwargs or len(kwargs) > 2:
            raise Exception('"name" and "value" are the required key arguments.')
        try:
            return Option.objects.get(name=kwargs['name'])
        except Option.DoesNotExist:
            return Option(**kwargs)

    def get(self, *args):
        """
        The site options are defined and saved by the OptionsForm fields,
        and this method ensures that some value or a default value will be
        returned when querying for an option value. `None` is returned if the
        option name is invalid.
        """

        if len(args) <= 0:
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
    created = models.DateTimeField(auto_now_add=True, editable=False, default='2001-01-01')
    updated = models.DateTimeField(auto_now=True, editable=False, default='2001-01-01')

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_criteria'

    def type(self):
        return _('criteria')

    def get_absolute_url(self, *args, **kwargs):
        return reverse('criteria', kwargs={'slug': self.slug })

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
    contributor = models.ManyToManyField(User, related_name='contributor', verbose_name=_('Contributors'), help_text=_('Users with permission to contribute to this problem.'), blank=True, null=True)
    manager = models.ManyToManyField(User, related_name='manager', verbose_name=_('Managers'), help_text=_('Users with permission to manage this problem.'), blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, editable=False, default='2000-01-01')
    updated = models.DateTimeField(auto_now=True, editable=False, default='2000-01-01')
    last_activity = models.DateTimeField(auto_now=True, editable=False, default='2000-01-01')

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_problem'

    def type(self):
        return _('problem')

    def get_absolute_url(self, *args, **kwargs):
        return reverse('problem', args=[self.slug])

    def revision_count(self):
        return reversion.get_for_object(self).count()

    def idea_count(self):
        return Idea.objects.filter(problem=self).count()

    def alternative_count(self):
        return Alternative.objects.filter(problem=self).count()

reversion.register(Problem)

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
    deleted_by = models.ForeignKey(User, editable=False, related_name='idea_deleted_by', null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False, default='2000-01-01')
    updated = models.DateTimeField(auto_now=True, editable=False, default='2000-01-01')

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_idea'

    def type(self):
        return _('idea')

    def get_absolute_url(self, *args, **kwargs):
        return reverse('idea', kwargs={'slug': self.problem.slug, 'pk': self.id})

    def revision_count(self):
        return reversion.get_for_object(self).count()

    def vote_count(self):
        w = Vote.objects.filter(idea=self).aggregate(models.Sum('weight'))['weight__sum']
        return w if w else 0

reversion.register(Idea)

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
    deleted_by = models.ForeignKey(User, editable=False, related_name='comment_deleted_by', null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False, default='2000-01-01')
    updated = models.DateTimeField(auto_now=True, editable=False, default='2000-01-01')

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_comment'

    def type(self):
        return _('comment')

class Message(models.Model):
    """
    Messages for users that managers can send to them.
    """

    problem = models.ForeignKey(Problem)
    sender = models.ForeignKey(User, related_name='message_sender')
    recipients = models.ManyToManyField(User, related_name='message_recipients')
    subject = models.TextField(verbose_name=_('Subject'))
    content = models.TextField(verbose_name=_('Content'))
    created = models.DateTimeField(auto_now_add=True, editable=False, default='2000-01-01')

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_message'

    def type(self):
        return _('message')

    def get_absolute_url(self, *args, **kwargs):
        return reverse('message', kwargs={'slug': self.problem.slug, 'pk': self.id })

    def get_message_recipients(self):
        """
        Fetches every user related to the problem: Author, managers,
        contributors, and commenters.
        """
        recipients = [self.problem.author]
        recipients = recipients + [user for user in self.problem.contributor.all()]
        recipients = recipients + [user for user in self.problem.manager.all()]
        for idea in Idea.objects.filter(problem=self.problem):
            recipients.append(idea.author)
            for comment in Comment.objects.filter(idea=idea):
                recipients.append(comment.author)
        return sorted(set(recipients))

class Alternative(models.Model):
    """
    Alternatives are the strategy table rows where ideas can be allocated.
    """

    problem = models.ForeignKey(Problem, editable=False)
    idea = models.ManyToManyField(Idea, editable=False, null=True, blank=True)
    order = models.PositiveSmallIntegerField(editable=False, default=0)
    created = models.DateTimeField(auto_now_add=True, editable=False, default='2001-01-01')

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_alternative'

    def type(self):
        return _('alternative')

    def fill_data(self, user=False):
        """
        Fill the alternative with problem and user-specific data.
        """
        self.total_ideas = self.idea.all().count()
        self.vote_count = Vote.objects.filter(alternative=self).count()
        self.voted = Vote.objects.filter(alternative=self, author=user).exists() if isinstance(user, User) else False
        self.criteria = list()
        for c in self.problem.criteria.all():
            c.total_stars = IdeaCriteria.objects.filter(idea__in=self.idea.all(), criteria=c).aggregate(stars=Sum('stars'))['stars']
            c.total_stars = c.total_stars if c.total_stars else 0
            c.star_ratio = c.total_stars * 100 / self.total_ideas / 5 if c.total_stars > 0 and self.total_ideas > 0 else 0
            self.criteria.append(c)

class Vote(models.Model):
    """
    A vote for idea or for an alternative.

    Attributes:
        * ``weight`` Vote weight. Negative only for ideas.
    """

    idea = models.ForeignKey(Idea, blank=True, null=True, related_name='vote_idea')
    comment = models.ForeignKey(Alternative, blank=True, null=True, related_name='vote_comment')
    alternative = models.ForeignKey(Alternative, blank=True, null=True, related_name='vote_alternative')
    author = models.ForeignKey(User)
    weight = models.SmallIntegerField(editable=False, default=0)
    created = models.DateTimeField(auto_now_add=True, editable=False, default='2001-01-01')

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_vote'

    def type(self):
        return _('vote')

class Activity(models.Model):
    """
    Abstract model to be filled by the ``ActivityManager`` class, where all
    that's being happening in the platform according to the viewer's
    permissions are fetched and listed.
    """

    problem = models.ForeignKey(Problem, blank=True, null=True)
    idea = models.ForeignKey(Idea, blank=True, null=True)
    comment = models.ForeignKey(Comment, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, blank=True, null=True)
    updated = models.DateTimeField(blank=True, null=True)

    class Meta:
        abstract = True
        managed = False

class ActivityManager(models.Manager):
    """
    Manager for retrieving activities from the database.
    """

    def type(self):
        return _('activity')

    def get_objects(self, *args, **kwargs):
        """
        Fetches activities related to problems, ideas and comments that can
        be publicy visible or can be accessed by the current user. That's a RAW
        SQL query that needs to work on all default engines.
        """

        # Query

        params = self.get_params(**kwargs)
        query = self.get_query_string()
        select = query['select'] % params
        limit = query['limit'] % params

        # Results

        query = select + limit
        cursor = connection.cursor()
        cursor.execute(query)

        dmp = _dmp.diff_match_patch()

        # Activity types

        re_problem = re.compile('^problem_[0-9]+')
        re_idea = re.compile('^idea_[0-9]+')
        re_comment = re.compile('^comment_[0-9]+')

        # Iterate

        activities = list()
        for q in cursor.fetchall():
            a = Activity()
            if re_problem.match(q[0]):
                a.problem = Problem.objects.get(id=q[1])
                obj = a.problem
            elif re_idea.match(q[0]):
                a.idea = Idea.objects.get(id=q[1])
                obj = a.idea
            elif re_comment.match(q[0]):
                a.comment = Comment.objects.get(id=q[1])
                obj = a.comment
            versions = reversion.get_for_object(obj)
            a.status = 'updated' if len(versions) > 1 else 'created'
            a.user = versions[1].revision.user if len(versions) > 1 else obj.author
            a.date = obj.updated
            if len(versions) > 1 and a.problem:
                diff = dmp.diff_main('<h3>' + versions[1].object_version.object.title + '</h3>' + versions[1].object_version.object.description, '<h3>' + a.problem.title + '</h3>' + a.problem.description)
                dmp.diff_cleanupSemantic(diff)
                a.detail = diff_prettyHtml(diff)
            activities.append(a)

        return activities

    def get_params(self, *args, **kwargs):
        """
        Supply the parameters for the activity query according to the DB
        engine.
        """

        db_engine = ''
        engine = settings.DATABASES['default']['ENGINE']
        if re.match('.*sqlite3$', engine):
            db_engine = 'sqlite3'
        elif re.match('.*psycopg2$', engine):
            db_engine = 'postgresql'
        elif re.match('.*mysql$', engine):
            db_engine = 'mysql'

        params = {
            'user': kwargs['user'] if 'user' in kwargs and int(kwargs['user']) else 0,
            'offset': kwargs['offset'] if 'offset' in kwargs and int(kwargs['offset']) else 0,
            'limit': kwargs['limit'] if 'limit' in kwargs and int(kwargs['limit']) < 5 else 10,
            'public': 'TRUE' if db_engine == 'postgresql' else '1',
            'prefix': settings.DNSTORM['table_prefix']
        }

        if 'page' in kwargs and int(kwargs['page']):
            params['page'] = int(kwargs['page'])
            params['offset'] = (int(kwargs['page']) - 1) * 10
            params['limit'] = 10

        return params

    def get_pagination(self, *args, **kwargs):
        """
        Gets pagination links for a given set of query variables.
        """

        # Total results count

        params = self.get_params(**kwargs)
        page = params['page'] if 'page' in params else 1
        total = self.get_total(**params)

        # Pagination

        pagination = dict()
        pagination['previous_page_number'] = page - 1 if page > 1 else 0
        pagination['next_page_number'] = page + 1 if (page + 1) * 10 < total else 0
        pagination['has_previous'] = True if pagination['previous_page_number'] else False
        pagination['has_next'] = True if pagination['next_page_number'] else False
        pagination['number'] = page
        pagination['paginator'] = { 'num_pages': total / 10 }
        return pagination


    def get_total(self, *args, **kwargs):
        """
        Fetchs only the total number of rows for an activity set. Used for
        pagination.
        """

        query = self.get_query_string()
        select = query['select'] % kwargs

        query = "SELECT COUNT(*) FROM (%(select)s) AS data" % { 'select': select }
        cursor = connection.cursor()
        cursor.execute(query)
        first = cursor.fetchone()
        return first[0] if len(first) > 0 else 0

    def get_query_string(self, *args, **kwargs):
        """
        Get the ``UNION`` SQL statement parts for the activity query.
        """

        return {
            'select': """
                    SELECT
                        'problem_' || p.id AS type,
                        p.id AS id,
                        p.updated AS date
                    FROM
                        %(prefix)s_problem p
                    WHERE 1=1
                        AND (
                            %(user)d = 0
                            OR p.author_id = %(user)d
                        )
                UNION
                    SELECT
                        'idea_' || i.id AS type,
                        i.id AS id,
                        i.updated AS date
                    FROM
                        %(prefix)s_idea i
                    LEFT JOIN
                        %(prefix)s_problem p
                        ON p.id = i.problem_id
                    WHERE 1=1
                        AND (
                            %(user)d = 0
                            OR i.author_id = %(user)d
                        )
                UNION
                    SELECT
                        'comment_' || c.id AS type,
                        c.id AS id,
                        c.updated AS date
                    FROM
                        %(prefix)s_comment c
                    LEFT JOIN
                        %(prefix)s_problem p
                        ON p.id = c.problem_id
                    LEFT JOIN
                        %(prefix)s_idea i
                        ON i.id = c.idea_id
                    WHERE 1=1
                        AND (
                            %(user)d = 0
                            OR c.author_id = %(user)d
                        )
                ORDER BY date DESC
            """,

            'limit': """
                LIMIT %(limit)d
                OFFSET %(offset)d
            """
        }
