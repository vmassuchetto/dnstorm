from datetime import datetime
from lib.slug import unique_slugify

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe

import settings
import reversion

from ckeditor.fields import RichTextField
from registration.signals import user_activated

class Criteria(models.Model):
    name = models.CharField(verbose_name=_('Name'), max_length=90)
    slug = models.CharField(max_length=90, unique=True)
    description = models.TextField(verbose_name=_('Description'), blank=True)
    order = models.IntegerField()
    created = models.DateTimeField(auto_now=True, editable=False)
    updated = models.DateTimeField(editable=False)

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_criteria'

    def __unicode__(self):
        return '<Criteria: %d>' % self.id

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
    locked = models.BooleanField(verbose_name=_('Locked'), help_text=_('Lock the problem so it will be kept visible but no one will be able to contribute.'), default=False, blank=True)
    blind = models.BooleanField(verbose_name=_('Blind contributions'), help_text=_('People can only see their own ideas.'), default=False, blank=True)
    max = models.IntegerField(verbose_name=_('Max ideas per user'), help_text=_('Leave 0 for unlimited ideas per user.'), default=0, blank=True)
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

reversion.register(Problem)
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
    author = models.ForeignKey(User, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        db_table = settings.DNSTORM['table_prefix'] + '_idea'

    def __unicode__(self):
        return '<Idea: %d>' % self.id

    def get_absolute_url(self, *args, **kwargs):
        return mark_safe('%s#idea-%d' % (reverse('problem', args=[self.problem.slug]), self.id))

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
