import re
from datetime import datetime
from dnstorm.app.lib.slug import unique_slugify

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models, connection
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe

import reversion
import diff_match_patch as _dmp
from dnstorm import settings
from dnstorm.app.lib.diff import diff_prettyHtml

from ckeditor.fields import RichTextField
from registration.signals import user_activated

reversion.register(User)

class Option(models.Model):
    """ Option is an adaptation for a meta-based table, where ``name`` is
    stored only once, and retrieved via the ``get`` method. """

    name = models.TextField(verbose_name=_('Name'), blank=False, unique=True)
    value = models.TextField(verbose_name=_('Value'), blank=False)

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_option'

    def __unicode__(self):
        return '<Option: %s>' % self.name

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
        """ The site options are defined and saved by the OptionsForm fields,
        and this method ensures that some value or a default value will be
        returned when querying for an option value. `None` is returned if the
        option name is invalid. """

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
        """ These are some default values that are used in templates and
        somewhere else. They are supposed to be overwritten by values on
        database. """

        return {
            'site_title': 'DNStorm',
            'site_description': _('An idea-generation platform')
        }

    def get_all(self):
        """ Get all the default values. """

        options = dict()
        defaults = self.get_defaults()
        for default in defaults:
            options[default] = self.get(default)
        return options

class Criteria(models.Model):
    """ When creating a problem, managers should define some criterias as a
    reference for the ideas submitted by users. These will also be the columns
    for the strategy table of the problem. """

    name = models.CharField(verbose_name=_('Name'), max_length=90)
    slug = models.CharField(max_length=90, unique=True)
    description = models.TextField(verbose_name=_('Description'), blank=True)
    order = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True, editable=False, default='2001-01-01')
    updated = models.DateTimeField(auto_now=True, editable=False, default='2001-01-01')

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_criteria'

    def __unicode__(self):
        return self.name

    def type(self):
        return _('criteria')

    def get_absolute_url(self, *args, **kwargs):
        return reverse('criteria', args=[self.slug])

    def problem_count(self):
        return Problem.objects.filter(criteria=self).count()

    def save(self, *args, **kwargs):
        self.slug = unique_slugify(self, self.name)
        super(Criteria, self).save(*args, **kwargs)

reversion.register(Criteria)

class Problem(models.Model):
    """ Problems are the central entity of the platform, as everything goes
    around them. This is no more than the suubject of discussion for generating
    ideas and a strategy table. """

    title = models.CharField(verbose_name=_('Title'), max_length=90)
    slug = models.SlugField(max_length=90, unique=True, editable=False)
    description = RichTextField(verbose_name=_('Description'), blank=True)
    criteria = models.ManyToManyField(Criteria, verbose_name=_('Criterias'), editable=False, blank=True, null=True)
    author = models.ForeignKey(User, related_name='author', editable=False)
    contributor = models.ManyToManyField(User, related_name='contributor', verbose_name=_('Contributors'), help_text=_('Users with permission to contribute to this problem.'), blank=True, null=True)
    manager = models.ManyToManyField(User, related_name='manager', verbose_name=_('Managers'), help_text=_('Users with permission to manage this problem.'), blank=True, null=True)
    open = models.BooleanField(verbose_name=_('Open participation'), help_text=_('Any registered user can contribute to this problem.'), default=True)
    public = models.BooleanField(verbose_name=_('Public'), help_text=_('The problem will be publicy available to anyone.'), default=True)
    locked = models.BooleanField(verbose_name=_('Locked'), help_text=_('Lock the problem so it will be kept visible but no one will be able to contribute.'), default=False, blank=True)
    blind = models.BooleanField(verbose_name=_('Blind contributions'), help_text=_('People can only see their own ideas.'), default=False, blank=True)
    max = models.IntegerField(verbose_name=_('Max ideas per user'), help_text=_('Maximum number of ideas an user will be able to contribute to this problem. Leave 0 for unlimited.'), default=0, blank=True)
    voting = models.BooleanField(verbose_name=_('Enable voting for ideas'), help_text=_('Users will be able to vote for the ideas.'), default=True, blank=True)
    vote_count = models.BooleanField(verbose_name=_('Display vote counts'), help_text=_('Users will be able to see how many votes each idea had.'), default=True, blank=True)
    vote_author = models.BooleanField(verbose_name=_('Display vote authors'), help_text=_('Ideas voting will be completely transparent.'), default=False, blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False, default='2000-01-01')
    updated = models.DateTimeField(auto_now=True, editable=False, default='2000-01-01')
    last_activity = models.DateTimeField(auto_now=True, editable=False, default='2000-01-01')

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_problem'

    def __unicode__(self):
        return u'%d' % self.id

    def type(self):
        return _('problem')

    def get_absolute_url(self, *args, **kwargs):
        return reverse('problem', args=[self.slug])

    def save(self, *args, **kwargs):
        self.slug = unique_slugify(self, self.title)
        super(Problem, self).save(*args, **kwargs)

    def revision_count(self):
        return reversion.get_for_object(self).count()

    def idea_count(self):
        return Idea.objects.filter(problem=self).count()

    def alternative_count(self):
        return Alternative.objects.filter(problem=self).count()

    def get_message_recipients(self):
        recipients = [self.author]
        recipients = recipients + [user for user in self.contributor.all()]
        recipients = recipients + [user for user in self.manager.all()]
        for idea in Idea.objects.filter(problem=self):
            recipients.append(idea.author)
            for comment in Comment.objects.filter(idea=idea):
                recipients.append(comment.author)
        return sorted(set(recipients))

reversion.register(Problem, follow=['criteria', 'contributor', 'manager'])

QUANTIFIER_CHOICES = (
    ('number', _('Number')),
    ('boolean', _('True or False')),
    ('text', _('Text')),
    ('daterange', _('Date range')))

class Quantifier(models.Model):
    """ Quantifiers is a pre-defined resource for ideas. By giving ideas, the
    users may quantify them if the manager asks for it. These quantifiers will
    also be calculated in the streategy table. """

    problem = models.ForeignKey(Problem, choices=QUANTIFIER_CHOICES, editable=False, blank=True, null=True)
    name = models.CharField(verbose_name=_('Name'), max_length=90)
    format = models.CharField(verbose_name=_('Type'), max_length=10)
    help = models.TextField(_('Help text'))

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_quantifier'

    def __unicode__(self):
        return u'%d' % self.id

    def type(self):
        return _('quantifier')

class Idea(models.Model):
    """ Ideas are the second main entity in the platform, as the
    problem-solving process requires idea generation and participation of
    users. These will after compose the strategy table. """

    title = models.CharField(verbose_name=_('title'), max_length=90)
    content = RichTextField(config_name='idea_content')
    problem = models.ForeignKey(Problem, editable=False)
    author = models.ForeignKey(User, editable=False)
    deleted_by = models.ForeignKey(User, editable=False, related_name='idea_deleted_by', null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False, default='2000-01-01')
    updated = models.DateTimeField(auto_now=True, editable=False, default='2000-01-01')

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_idea'

    def __unicode__(self):
        return '<Idea>'

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

class QuantifierValue(models.Model):
    """ Values for quantifiers in a meta-key schema. """

    quantifier = models.ForeignKey(Quantifier)
    idea = models.ForeignKey(Idea)
    value = models.TextField(verbose_name=_('value'))

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_quantifier_value'

    def __unicode__(self):
        return '<QuantifierValue>'

    def type(self):
        return _('quantifier value')

class Comment(models.Model):
    """ Comments that can be made for ideas or problems. """

    problem = models.ForeignKey(Problem, editable=False, blank=True, null=True)
    idea = models.ForeignKey(Idea, editable=False, blank=True, null=True)
    content = models.TextField(verbose_name=_('Comment'))
    author = models.ForeignKey(User, editable=False)
    deleted_by = models.ForeignKey(User, editable=False, related_name='comment_deleted_by', null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False, default='2000-01-01')
    updated = models.DateTimeField(auto_now=True, editable=False, default='2000-01-01')

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_comment'

    def __unicode__(self):
        return '<Comment: %d>' % self.id

    def type(self):
        return _('comment')

reversion.register(Comment)

class Message(models.Model):
    """ Messages for users that managers can send to them. """

    problem = models.ForeignKey(Problem)
    sender = models.ForeignKey(User)
    subject = models.TextField(verbose_name=_('Subject'))
    content = models.TextField(verbose_name=_('Content'))
    created = models.DateTimeField(auto_now_add=True, editable=False, default='2000-01-01')

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_message'

    def __unicode__(self):
        return '<Message: %d>' % self.id

    def type(self):
        return _('message')

    def get_absolute_url(self, *args, **kwargs):
        return reverse('message', kwargs={'slug': self.problem.slug, 'pk': self.id })

reversion.register(Message)

class Alternative(models.Model):
    """ Alternatives are the strategy table rows where ideas can be allocated.
    If there's no criteria in the problem, these will be just rows with no
    specific columns. """

    problem = models.ForeignKey(Problem)
    name = models.TextField(verbose_name=_('Name'))
    description = models.TextField(verbose_name=_('Description'))
    order = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True, editable=False, default='2001-01-01')
    updated = models.DateTimeField(auto_now=True, editable=False, default='2001-01-01')

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_alternative'

    def __unicode__(self):
        return '<Alternative: %d>' % self.id

    def type(self):
        return _('alternative')

    def get_items(self):
        items = list()
        criterias = Criteria.objects.filter(problem=self.problem)
        if criterias:
            for criteria in criterias:
                try:
                    items.append({
                        'criteria': criteria,
                        'objects': AlternativeItem.objects.filter(criteria=criteria, alternative=self)
                    })
                except:
                    pass

        else:
            items.append({
                'criteria': None,
                'objects': AlternativeItem.objects.filter(criteria=None, alternative=self)
            })
        return items

    def get_quantifiers(self):
        quantifiers = dict()
        items = self.get_items()
        for item in items:
            for alternative_item in item['objects']:
                for idea in alternative_item.idea.all():
                    for q in idea.quantifiervalue_set.all():
                        if q.quantifier.format not in ['number', 'boolean']:
                            continue
                        k = q.quantifier.id
                        if k not in quantifiers.keys():
                            quantifiers[k] = q.quantifier
                            quantifiers[k].value = 0
                            quantifiers[k].count = 0
                        if q.quantifier.format == 'boolean':
                            quantifiers[k].value += bool(q.value)
                            quantifiers[k].count += 1
                        elif q.quantifier.format == 'number':
                            quantifiers[k].value += int(q.value)
        return quantifiers

class AlternativeItem(models.Model):
    """ Ideas mapping in the strategy table allocated by some criteria and some
    alternative. """

    criteria = models.ForeignKey(Criteria, blank=True, null=True)
    alternative = models.ForeignKey(Alternative)
    idea = models.ManyToManyField(Idea)
    name = models.TextField(verbose_name=_('Name'))
    order = models.IntegerField()

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_alternative_item'

    def __unicode__(self):
        return '<AlternativeItem>'

    def type(self):
        return _('alternative item')

    def save(self, *args, **kwargs):
        self.order = self.order if self.order else 0
        super(AlternativeItem, self).save(*args, **kwargs)

class Vote(models.Model):
    """ A vote for idea or for an alternative. """

    idea = models.ForeignKey(Idea, blank=True, null=True)
    alternative = models.ForeignKey(Alternative, blank=True, null=True)
    author = models.ForeignKey(User)
    weight = models.SmallIntegerField(choices=(
        (1, _('Upvote')),
        (-1, _('Downvote'))))
    date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_vote'

    def __unicode__(self):
        return '<Vote: %d>' % self.id

    def type(self):
        return _('vote')

class Activity(models.Model):
    """ Abstract model to be filled by the ``ActivityManager`` class, where all
    that's being happening in the platform according to the viewer's
    permissions are fetched and listed. """

    problem = models.ForeignKey(Problem, blank=True, null=True)
    idea = models.ForeignKey(Idea, blank=True, null=True)
    comment = models.ForeignKey(Comment, blank=True, null=True)
    detail = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)

    class Meta:
        abstract = True
        managed = False

class ActivityManager(models.Manager):
    """ Manager for retrieving activities from the database. """

    def type(self):
        return _('activity')

    def get_objects(self, *args, **kwargs):
        """ Fetches activities related to problems, ideas and comments that can
        be publicy visible or can be accessed by the current user. That's a RAW
        SQL query that needs to work on all default engines. """

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
        """ Supply the parameters for the activity query according to the DB
        engine. """

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
        """ Gets pagination links for a given set of query variables. """

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
        """ Fetchs only the total number of rows for an activity set. Used for
        pagination. """

        query = self.get_query_string()
        select = query['select'] % kwargs

        query = "SELECT COUNT(*) FROM (%(select)s) AS data" % { 'select': select }
        cursor = connection.cursor()
        cursor.execute(query)
        first = cursor.fetchone()
        return first[0] if len(first) > 0 else 0

    def get_query_string(self, *args, **kwargs):
        """ Get the ``UNION`` SQL statement parts for the activity query. """

        return {
            'select': """
                    SELECT
                        'problem_' || p.id AS type,
                        p.id AS id,
                        p.updated AS date
                    FROM
                        %(prefix)s_problem p
                    WHERE 1=1
                        AND p.public = %(public)s
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
                        AND p.public = %(public)s
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
                        AND p.public = %(public)s
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
