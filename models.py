from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _

from datetime import datetime
from utils.unique_slugify import unique_slugify
import settings

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
    user = models.ManyToManyField(User, related_name='user', verbose_name=_('Users'), help_text=_('Users with permission to contribute to this problem.'), blank=True, null=True)
    manager = models.ManyToManyField(User, related_name='admin', verbose_name=_('Admins'), help_text=_('Users with permission to manage this problem.'), blank=True, null=True)
    open = models.BooleanField(verbose_name=_('Open participation'), help_text=_('Any registered user can contribute to this problem.'), default=True)
    public = models.BooleanField(verbose_name=_('Public'), help_text=_('The problem will be publicy available to anyone.'), default=True)
    max = models.IntegerField(verbose_name=_('Max ideas per user.'), help_text=_('Leave 0 for unlimited ideas per user.'), default=0, blank=True)
    revision = models.ForeignKey('self', editable=False, blank=True, null=True)
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
        return Problem.objects.filter(revision=self.id).count()

    def idea_count(self):
        return Idea.objects.filter(problem=self).count()

class Idea(models.Model):
    content = RichTextField(config_name='idea_content')
    problem = models.ForeignKey(Problem, editable=False)
    user = models.ForeignKey(User, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    def __unicode__(self):
        return u'%s' % self.id

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_idea'

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = datetime.today()
        self.updated = datetime.today()
        super(Idea, self).save(*args, **kwargs)
