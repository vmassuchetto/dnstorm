from datetime import datetime
from lib.slug import unique_slugify

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _

import settings
import reversion

from ckeditor.fields import RichTextField

class Criteria(models.Model):
    name = models.CharField(verbose_name=_('Name'), max_length=90)
    slug = models.CharField(max_length=90, unique=True)
    description = models.TextField(verbose_name=_('Description'), blank=True)
    order = models.IntegerField()
    created = models.DateTimeField(auto_now=True, editable=False)
    updated = models.DateTimeField(editable=False)

    def __unicode__(self):
        return self.slug

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_criteria'

    def get_absolute_url(self, *args, **kwargs):
        return reverse('problem', args=[self.slug])

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = datetime.today()
        self.updated = datetime.today()
        self.slug = unique_slugify(self, self.name)
        if not self.order:
            self.order = 0
        super(Criteria, self).save(*args, **kwargs)

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
    max = models.IntegerField(verbose_name=_('Max ideas per user'), help_text=_('Leave 0 for unlimited ideas per user.'), default=0, blank=True)
    locked = models.BooleanField(verbose_name=_('Locked'), help_text=_('Lock the problem so no one will be able to contribute.'), default=False, blank=True)
    voting = models.BooleanField(verbose_name=_('Enable voting for ideas'), help_text=_('Users will be able to vote for the ideas.'), default=True, blank=True)
    vote_count = models.BooleanField(verbose_name=_('Display vote counts'), help_text=_('Users will be able to see how many votes each idea had.'), default=True, blank=True)
    vote_author = models.BooleanField(verbose_name=_('Display vote authors'), help_text=_('Ideas voting will be completely transparent.'), default=False, blank=True)
    modified = models.DateTimeField(auto_now=True, editable=False)

    def __unicode__(self):
        return self.title

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_problem'

    def get_absolute_url(self, *args, **kwargs):
        return reverse('problem', args=[self.slug])

    def save(self, *args, **kwargs):
        self.slug = unique_slugify(self, self.title)
        super(Problem, self).save(*args, **kwargs)

    def revision_count(self):
        return reversion.get_for_object(self).count()

    def idea_count(self):
        return Idea.objects.filter(problem=self).count()

reversion.register(Problem)

class Idea(models.Model):
    content = RichTextField(config_name='idea_content')
    problem = models.ForeignKey(Problem, editable=False)
    author = models.ForeignKey(User, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    def __unicode__(self):
        return u'%s' % self.id

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_idea'

    def revision_count(self):
        return reversion.get_for_object(self).count()

    def vote_count(self):
        w = Vote.objects.filter(idea=self).aggregate(models.Sum('weight'))['weight__sum']
        return w if w else 0

reversion.register(Idea)

class Comment(models.Model):
    idea = models.ForeignKey(Idea, editable=False, blank=True, null=True)
    content = models.TextField(verbose_name=_('Comment'))
    author = models.ForeignKey(User, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    def __unicode__(self):
        return u'%s (Idea: %s)' % (self.author.username, self.idea.id)

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_comment'

reversion.register(Comment)

class Message(models.Model):
    problem = models.ForeignKey(Problem)
    content = models.TextField(verbose_name=_('Content'))
    modified = models.DateTimeField(auto_now=True, editable=False)

    def __unicode__(self):
        return u'%s (Problem: %d)' % (self.subject, self.problem.id)

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_message'

reversion.register(Message)

class Vote(models.Model):
    idea = models.ForeignKey(Idea)
    author = models.ForeignKey(User)
    weight = models.SmallIntegerField(choices=(
        (1, _('Upvote')),
        (-1, _('Downvote'))))
    date = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '%s (Idea: %s) (Type: %d)' % (self.user, self.idea, self.weight)

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_vote'

class Alternative(models.Model):
    problem = models.ForeignKey(Problem)
    title = models.TextField(verbose_name=_('Label'))
    description = models.TextField(verbose_name=_('Description'))
    order = models.IntegerField()

    def __unicode__(self):
        return '%s (Problem: %s)' % (self.title, self.problem.title)

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_alternative'

    def get_items(self):
        items = list()
        criterias = Criteria.objects.filter(problem=self.problem)
        for criteria in criterias:
            try:
                items.append({
                    'criteria': criteria,
                    'object': AlternativeItem.objects.get(criteria=criteria, alternative=self) })
            except:
                items.append({
                    'criteria': criteria,
                    'object': False })
        return items


class AlternativeItem(models.Model):
    criteria = models.ForeignKey(Criteria)
    alternative = models.ForeignKey(Alternative)
    idea = models.ForeignKey(Idea)
    title = models.TextField(verbose_name=_('Label'))

    def __unicode__(self):
        return '%d (Criteria: %s) (Alternative: %s)' % (self.id, self.criteria.title, self.alternative.title)

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_alternative_item'
