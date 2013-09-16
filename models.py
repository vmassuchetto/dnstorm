from datetime import datetime
from lib.slug import unique_slugify

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _

import settings
import reversion

from ckeditor.fields import RichTextField

class Tag(models.Model):
    name = models.CharField(verbose_name=_('Name'), max_length=90)
    slug = models.CharField(max_length=90, unique=True)
    description = models.TextField(verbose_name=_('Description'), blank=True)
    created = models.DateTimeField(auto_now=True, editable=False)
    updated = models.DateTimeField(editable=False)

    def __unicode__(self):
        return self.slug

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_tag'

    def get_absolute_url(self, *args, **kwargs):
        return reverse('problem', args=[self.slug])

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = datetime.today()
        self.updated = datetime.today()
        unique_slugify(self, self.title)
        super(Tag, self).save(*args, **kwargs)

class Problem(models.Model):
    title = models.CharField(verbose_name=_('Title'), max_length=90)
    slug = models.SlugField(max_length=90, unique=True, editable=False)
    description = RichTextField(verbose_name=_('Description'), blank=True)
    tag = models.ManyToManyField(Tag, verbose_name=_('Tags'), editable=False, blank=True, null=True)
    author = models.ForeignKey(User, related_name='author', editable=False)
    contributor = models.ManyToManyField(User, related_name='contributor', verbose_name=_('Contributors'), help_text=_('Users with permission to contribute to this problem.'), blank=True, null=True)
    manager = models.ManyToManyField(User, related_name='manager', verbose_name=_('Managers'), help_text=_('Users with permission to manage this problem.'), blank=True, null=True)
    open = models.BooleanField(verbose_name=_('Open participation'), help_text=_('Any registered user can contribute to this problem.'), default=True)
    public = models.BooleanField(verbose_name=_('Public'), help_text=_('The problem will be publicy available to anyone.'), default=True)
    max = models.IntegerField(verbose_name=_('Max ideas per user.'), help_text=_('Leave 0 for unlimited ideas per user.'), default=0, blank=True)
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
        return u'%d (Idea: %s) (Author: %s)' % (self.id, self.idea.id, self.author.username)

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_comment'

reversion.register(Comment)

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

