import json
import re
import urlparse

from django import forms
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import Http404, QueryDict
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from ajax_select.fields import AutoCompleteSelectMultipleField
from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import *
from registration.forms import RegistrationFormUniqueEmail

from dnstorm.app import models
from dnstorm.app.utils import get_object_or_none, get_option
from dnstorm.settings import LANGUAGES

class RegistrationForm(RegistrationFormUniqueEmail):
    hash = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        _hash = kwargs.pop('hash') if 'hash' in kwargs else None
        self.helper = FormHelper()
        self.helper.form_action = '.'
        self.helper.layout = Layout(
            'username',
            'email',
            'password1',
            'password2',
            'hash',
            ButtonHolder(
                Submit('submit', _('Register'), css_class='radius expand'),
            ),
        )
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['hash'].initial = _hash if _hash else 0

class AdminOptionsForm(forms.Form):
    site_title = forms.CharField(label=_('Site title'), help_text=_('Page title for browsers'))
    site_url = forms.CharField(label=_('Site URL'), help_text=_('Site domain for URL generation with http scheme. Examples: \'http://domain.com\', \'https://subdomain.domain.com\', \'http://domain:port\''))

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_action = '.'
        self.helper.layout = Layout(
            Fieldset(_('Site'),
                'site_title',
                'site_url',
            ),
            ButtonHolder(
                Submit('submit', _('Save'), css_class='right radius'),
            ),
        )
        super(AdminOptionsForm, self).__init__(*args, **kwargs)

        # Form defaults or saved values

        for field in self.fields:
            self.fields[field].initial = get_option(field)

    def clean_site_url(self):
        url = urlparse.urlparse(self.cleaned_data['site_url'])
        if not url.netloc:
            raise forms.ValidationError(_('Wrong domain format.'))
        return self.cleaned_data['site_url']


class AdminUserForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_superuser']

    def __init__(self, *args, **kw):
        super(UserAdminForm, self).__init__(*args, **kw)
        if self.instance.is_active:
            actions = HTML('<a data-reveal-id="deactivate-modal" data-reveal href="javascript:void(0)" class="left button secondary tiny radius alert">' + _('Deactivate account') + '</a>')
        else:
            actions = HTML('<a data-reveal-id="activate-modal" data-reveal href="javascript:void(0)" class="left button secondary tiny radius success">' + _('Activate account') + '</a>')
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(_('Edit user "%s"' % self.instance.username),
                'username',
                'email',
                'first_name',
                'last_name',
                'is_superuser',
                ButtonHolder(
                    actions,
                    Submit('submit', _('Save'), css_class='right radius'),
                ),
            )
        )

class ProblemForm(forms.ModelForm):
    criteria = AutoCompleteSelectMultipleField('criteria', required=True)

    class Meta:
        model = models.Problem

    def __init__(self, *args, **kwargs):
        self.instance = kwargs['instance'] if 'instance' in kwargs else False
        self.helper = FormHelper()
        self.helper.form_action = '.'
        self.helper.form_class = 'problem-form'
        self.helper.layout = Layout(
            Fieldset('<i class="fi-puzzle"></i>&nbsp;' + _('Problem description'),
                'title',
                'description',
            ),
            Fieldset('<i class="fi-target-two"></i>&nbsp;' + _('Criterias'),
                'criteria',
            ),
            Fieldset('<i class="fi-lock"></i>&nbsp;' + _('Permissions'),
                'public',
            ),
            ButtonHolder(
                Submit('submit', _('Save'), css_class='right radius'),
            ),
        )
        super(ProblemForm, self).__init__(*args, **kwargs)

        if self.instance.id:
            self.fields['criteria'].initial = [c.id for c in self.instance.criteria.all()]

class ContributorForm(forms.Form):
    contributor = AutoCompleteSelectMultipleField('user', required=False)
    problem = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):

        if not dict(kwargs).setdefault('problem', None):
            raise Exception('Wrong kwargs for ContributorForm')
        problem = get_object_or_404(models.Problem, id=kwargs['problem'])
        kwargs.pop('problem')

        # Invitations section HTML

        invitations_html = list()
        invitations = models.Invitation.objects.filter(problem=problem).order_by('email')

        for i in invitations:
            u = User(username=i.email, email=i.email)
            u.invitation = i.id
            invitations_html.append(render_to_string('user_lookup_display.html', {'user': u}))

        invitations_html = '<div id="pending-invitations"><h6>%s</h6>%s</div>' % (_('Pending invitations'), ''.join(invitations_html)) if len(invitations) > 0 else ''

        self.helper = FormHelper()
        self.helper.form_action = '.'
        self.helper.layout = Layout(
            'contributor',
            'problem',
            Row(Column(HTML(invitations_html))),
            Row(Column(
                Submit('submit', _('Save'), css_class='right radius'), css_class='large-12 top-1em',
            )),
        )
        super(ContributorForm, self).__init__(*args, **kwargs)
        self.fields['problem'].initial = problem.id
        self.fields['contributor'].initial = [c.id for c in problem.contributor.all()]

class CriteriaForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea(attrs={'id': 'criteria_description'}))

    class Meta:
        model = models.Criteria
        exclude = ['slug']

    def __init__(self, *args, **kwargs):
        star = '<i class="fi-star"></i>'
        self.helper = FormHelper()
        self.helper.form_action = '.'
        layout_args = (
            Row(Column('name', css_class='large-12')),
            Row(Column('description', css_class='large-12')),
            'id',
            Row(Column(HTML('<h4>' + _('Quantification') + '</h4>'), css_class='large-12')),
            Row(Column(HTML('<p class="formHint quantifier-help">' + _('Users will use 5 stars to rate how ideas match each criteria. Describe what each number of star means.') + '</p>'), css_class="large-12"))
        )
        for i in range(1,6):
            layout_args += (Row(Column(HTML('<label class="right inline">' + star * i + '</label>'), css_class='large-2'), Column(Field('help_star%d' % i), css_class='large-10')),)
        layout_args += (ButtonHolder(
            Submit('submit', _('Save'), css_class='right radius'),
        ),)
        self.helper.layout = Layout(*layout_args)
        super(CriteriaForm, self).__init__(*args, **kwargs)
        for i in range(1,6):
            self.fields['help_star%d' % i].label = ''

class IdeaForm(forms.ModelForm):
    problem = forms.IntegerField()

    class Meta:
        model = models.Idea

    def __init__(self, *args, **kwargs):

        # There must always be a problem associated to an idea

        self.problem = None
        if len(args) > 0 and isinstance(args[0], QueryDict):
            idea = None
            self.problem = get_object_or_none(models.Problem, id=args[0].get('problem', None))

        if not self.problem \
            and 'problem' in kwargs \
            and isinstance(kwargs['problem'], models.Problem):
            idea = None
            self.problem = kwargs['problem']
            del kwargs['problem']
        elif not self.problem \
            and 'problem' in kwargs \
            and (isinstance(kwargs['problem'], int) \
                or isinstance(kwargs['problem'], str)):
            idea = None
            self.problem = get_object_or_none(models.Problem, id=kwargs['problem'])
        elif not self.problem \
            and 'instance' in kwargs \
            and isinstance(kwargs['instance'], models.Idea):
            idea = kwargs['instance']
            self.problem = idea.problem

        if not self.problem:
            raise Http404

        super(IdeaForm, self).__init__(*args, **kwargs)

        criteria_html = tuple()
        criteria_fields = tuple()
        context = dict()

        # Problem identifier

        criteria_fields += (Field('problem', value=self.problem.id, type='hidden'),)

        # Dynamically add the criteria star fields as integers

        for c in self.problem.criteria.all():
            context['criteria'] = c
            s = get_object_or_none(models.IdeaCriteria, idea=idea, criteria=c)
            context['stars'] = s.stars if s else 0
            criteria_html += (HTML(render_to_string('criteria_vote.html', context)),)
            self.fields['criteria_%d' % c.id] = forms.IntegerField(label=c.name, initial=context['stars'])
            criteria_fields += (Field('criteria_%d' % c.id, type='hidden'),)

        title = _('Edit your idea') if idea else _('Give your idea')
        layout_args = (
            HTML('<h3>' + title + '</h3>'),
            'title',
            'content',
            HTML('<h5 class="top-1em">' + _('How this idea meet the problem criterias') + '</h5>')) \
                + criteria_html \
                + criteria_fields \
                + (Submit('submit', _('Submit'), css_class='right radius'),)

        # Form instantiation

        self.helper = FormHelper()
        self.helper.form_action = '.'
        self.helper.layout = Layout(*layout_args)

    def clean(self):

        # All criteria quantifications are required

        for c in self.problem.criteria.all():
            f = 'criteria_%d' % c.id
            if f not in self.cleaned_data or self.cleaned_data[f] == 0:
                raise forms.ValidationError(_('You need to provide a number of stars for all criterias.'))

        return self.cleaned_data

class CommentForm(forms.ModelForm):
    idea = forms.IntegerField()
    problem = forms.IntegerField()
    content = forms.CharField(widget=forms.Textarea(attrs={'id': 'comment_content'}))

    class Meta:
        model = models.Comment

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_action = '.'
        self.helper.layout = Layout(
            Field('problem', type='hidden'),
            Field('idea', type='hidden'),
            Row(
                Column('content', css_class='large-10'),
                Column(Submit('submit', _('Submit'), css_class='button small radius'), css_class='large-2 alignright'),
            )
        )
        super(CommentForm, self).__init__(*args, **kwargs)
        self.fields['content'].label = ''

class AlternativeForm(forms.Form):
    problem = forms.IntegerField()
    name = forms.CharField(label=_('Title'))
    description = forms.CharField(label=_('Description'), widget=forms.Textarea)
    mode = forms.CharField()
    object = forms.CharField()

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_action = '.'
        self.helper.layout = Layout(
            'name',
            'description',
            Field('mode', type='hidden'),
            Field('object', type='hidden'),
            Field('problem', type='hidden'),
            ButtonHolder(
                Submit('submit', _('Save'), css_class='right radius'),
            ),
        )
        super(AlternativeForm, self).__init__(*args, **kwargs)
