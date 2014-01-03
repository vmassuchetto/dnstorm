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

class Option(models.Model):
    name = models.TextField(verbose_name=_('Name'), blank=False, unique=True)
    value = models.TextField(verbose_name=_('Value'), blank=False)

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_option'

    def __unicode__(self):
        return '<Option: %s>' % self.name

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
        except:
            defaults = self.get_defaults()
            if args[0] not in defaults:
                return None
            value = defaults[args[0]]
        return value

    def get_defaults(self, *args, **kwargs):
        return {
            'site_title': 'DNStorm',
            'site_description': _('An idea-generation platform')
        }

    def get_all(self):
        options = dict()
        defaults = self.get_defaults()
        for default in defaults:
            options[default] = self.get(default)
        return options

class Criteria(models.Model):
    name = models.CharField(verbose_name=_('Name'), max_length=90)
    parent = models.ForeignKey('self', verbose_name=_('Parent'), blank=True, null=True)
    slug = models.CharField(max_length=90, unique=True)
    description = models.TextField(verbose_name=_('Description'), blank=True)
    order = models.IntegerField()
    created = models.DateTimeField(auto_now=True, editable=False)
    updated = models.DateTimeField(editable=False)

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_criteria'

    def __unicode__(self):
        return self.name

    def get_absolute_url(self, *args, **kwargs):
        return reverse('criteria', args=[self.slug])

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = datetime.today()
        self.updated = datetime.today()
        self.slug = unique_slugify(self, self.name)
        if not self.order:
            self.order = 0
        super(Criteria, self).save(*args, **kwargs)

reversion.register(Criteria)

class Problem(models.Model):
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
    modified = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_problem'

    def __unicode__(self):
        return '<Problem: %d>' % self.id

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

    def invites_handler(sender, user, request, *args, **kwargs):
        """ After the user is activated we need to search for previous invites
        for participating in problems he received and then add it back as a
        contributor. """
        invites = Invite.objects.filter(email=user.email)
        for i in invites:
            i.problem.contributor.add(user)
        invites.delete()

reversion.register(Problem, follow=['criteria', 'contributor', 'manager'])
user_activated.connect(Problem.invites_handler)

class Invite(models.Model):
    problem = models.ForeignKey(Problem)
    email = models.TextField()

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_problem_invite'

    def __unicode__(self):
        return '<ProblemInvite>'

class Idea(models.Model):
    title = models.CharField(verbose_name=_('Title'), max_length=90)
    content = RichTextField(config_name='idea_content')
    problem = models.ForeignKey(Problem, editable=False)
    cost = models.IntegerField(verbose_name=_('Cost'), blank=True, null=True)
    deadline = models.IntegerField(verbose_name=_('Deadline'), blank=True, null=True)
    author = models.ForeignKey(User, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_idea'

    def __unicode__(self):
        return '<Idea: %d>' % self.id

    def get_absolute_url(self, *args, **kwargs):
        return reverse('idea', kwargs={'slug':self.problem.slug, 'pk': self.id})

    def revision_count(self):
        return reversion.get_for_object(self).count()

    def vote_count(self):
        w = Vote.objects.filter(idea=self).aggregate(models.Sum('weight'))['weight__sum']
        return w if w else 0

reversion.register(Idea)

class Comment(models.Model):
    problem = models.ForeignKey(Problem, editable=False, blank=True, null=True)
    idea = models.ForeignKey(Idea, editable=False, blank=True, null=True)
    content = models.TextField(verbose_name=_('Comment'))
    author = models.ForeignKey(User, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_comment'

    def __unicode__(self):
        return '<Comment: %d>' % self.id

reversion.register(Comment)

class Message(models.Model):
    problem = models.ForeignKey(Problem)
    sender = models.ForeignKey(User)
    subject = models.TextField(verbose_name=_('Subject'))
    content = models.TextField(verbose_name=_('Content'))
    modified = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_message'

    def __unicode__(self):
        return '<Message: %d>' % self.id

    def get_absolute_url(self, *args, **kwargs):
        return reverse('message', args=[self.id])

reversion.register(Message)

class Vote(models.Model):
    idea = models.ForeignKey(Idea)
    author = models.ForeignKey(User)
    weight = models.SmallIntegerField(choices=(
        (1, _('Upvote')),
        (-1, _('Downvote'))))
    date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_vote'

    def __unicode__(self):
        return '<Vote: %d>' % self.id

class Alternative(models.Model):
    problem = models.ForeignKey(Problem)
    name = models.TextField(verbose_name=_('Name'))
    description = models.TextField(verbose_name=_('Description'))
    order = models.IntegerField()
    created = models.DateTimeField(auto_now=True, editable=False)
    updated = models.DateTimeField(editable=False)

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_alternative'

    def __unicode__(self):
        return '<Alternative: %d>' % self.id

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

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = datetime.today()
        self.updated = datetime.today()
        if not self.order:
            self.order = 0
        super(Alternative, self).save(*args, **kwargs)


class AlternativeItem(models.Model):
    criteria = models.ForeignKey(Criteria, blank=True, null=True)
    alternative = models.ForeignKey(Alternative)
    idea = models.ManyToManyField(Idea)
    name = models.TextField(verbose_name=_('Name'))
    order = models.IntegerField()

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_alternative_item'

    def __unicode__(self):
        return '<AlternativeItem>'

    def save(self, *args, **kwargs):
        self.order = self.order if self.order else 0
        super(AlternativeItem, self).save(*args, **kwargs)

class Activity(models.Model):
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

    def get(self, *args, **kwargs):
        """ Fetchs activities related to problems, ideas and comments that can
        be publicy visible or can be accessed by the current user. """

        user = kwargs['user'] if 'user' in kwargs and int(kwargs['user']) else 0
        offset = kwargs['offset'] if 'offset' in kwargs and int(kwargs['offset']) else 0
        limit = kwargs['limit'] if 'limit' in kwargs and int(kwargs['limit']) else 10

        db_engine = ''
        engine = settings.DATABASES['default']['ENGINE']
        if re.match('.*sqlite3$', engine):
            db_engine = 'sqlite3'
        elif re.match('.*psycopg2$', engine):
            db_engine = 'postgresql'
        elif re.match('.*mysql$', engine):
            db_engine = 'mysql'

        cursor = connection.cursor()
        cursor.execute("""
                SELECT
                    'problem_' || p.id AS type,
                    p.id AS id,
                    p.modified AS date
                FROM
                    %(dnstorm)s_problem p
                LEFT JOIN
                    %(dnstorm)s_problem_contributor pc
                    ON p.id = pc.problem_id
                LEFT JOIN
                    %(dnstorm)s_problem_manager pm
                    ON p.id = pm.problem_id
                WHERE 1=1
                    OR p.public = %(public)s
                    OR p.author_id = %(user)d
                    OR pc.user_id = %(user)d
                    OR pm.user_id = %(user)d
            UNION
                SELECT
                    'idea_' || i.id as type,
                    i.id AS id,
                    i.modified AS date
                FROM
                    %(dnstorm)s_idea i
                LEFT JOIN
                    %(dnstorm)s_problem p
                    ON p.id = i.problem_id
                LEFT JOIN
                    %(dnstorm)s_problem_contributor pc
                    ON p.id = pc.problem_id
                LEFT JOIN
                    %(dnstorm)s_problem_manager pm
                    ON p.id = pm.problem_id
                WHERE 1=1
                    OR i.author_id = %(user)d
                    OR p.public = %(public)s
                    OR p.author_id = %(user)d
                    OR pc.user_id = %(user)d
                    OR pm.user_id = %(user)d
            UNION
                SELECT
                    'comment_' || c.id as type,
                    c.id AS id,
                    c.modified AS date
                FROM
                    %(dnstorm)s_comment c
                LEFT JOIN
                    %(dnstorm)s_problem p
                    ON p.id = c.problem_id
                LEFT JOIN
                    %(dnstorm)s_idea i
                    ON i.id = c.idea_id
                LEFT JOIN
                    %(dnstorm)s_problem_contributor pc
                    ON p.id = pc.problem_id
                LEFT JOIN
                    %(dnstorm)s_problem_manager pm
                    ON p.id = pm.problem_id
                LEFT JOIN
                    %(dnstorm)s_problem p2
                    ON p2.id = i.problem_id
                LEFT JOIN
                    %(dnstorm)s_problem_contributor pc2
                    ON p2.id = pc2.problem_id
                LEFT JOIN
                    %(dnstorm)s_problem_manager pm2
                    ON p2.id = pm2.problem_id
                WHERE 1=1
                    OR c.author_id = %(user)d
                    OR i.author_id = %(user)d
                    OR p.public = %(public)s
                    OR p.author_id = %(user)d
                    OR pc.user_id = %(user)d
                    OR pm.user_id = %(user)d
                    OR p2.public = %(public)s
                    OR p2.author_id = %(user)d
                    OR pc2.user_id = %(user)d
                    OR pm2.user_id = %(user)d
            ORDER BY date DESC
            LIMIT %(limit)d
            OFFSET %(offset)d
        """ % {
            'dnstorm': settings.DNSTORM['table_prefix'],
            'user': user,
            'offset': offset,
            'limit': limit,
            'public': 'TRUE' if db_engine == 'postgresql' else '1'
        })

        dmp = _dmp.diff_match_patch()

        re_problem = re.compile('^problem_[0-9]+')
        re_idea = re.compile('^idea_[0-9]+')
        re_comment = re.compile('^comment_[0-9]+')

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
            a.date = obj.modified
            if len(versions) > 1 and a.problem:
                diff = dmp.diff_main('<h3>' + versions[1].object_version.object.title + '</h3>' + versions[1].object_version.object.description, '<h3>' + a.problem.title + '</h3>' + a.problem.description)
                dmp.diff_cleanupSemantic(diff)
                a.detail = diff_prettyHtml(diff)
            activities.append(a)

        return activities
