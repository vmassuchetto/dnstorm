import re
import json

from django import forms
from django.http import Http404, QueryDict
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404

from dnstorm.settings import LANGUAGES
from dnstorm.app import models
from dnstorm.app.lib.get import get_object_or_none

from ajax_select.fields import AutoCompleteSelectMultipleField
from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import *
from registration.forms import RegistrationFormUniqueEmail

class AdminOptionsForm(forms.Form):
    site_title = forms.CharField(label=_('Site title'))
    site_description = forms.CharField(label=_('Site description'))

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_action = '.'
        self.helper.layout = Layout(
            Fieldset(_('Site'),
                'site_title',
                'site_description'
            ),
            ButtonHolder(
                Submit('submit', _('Save'), css_class='radius'),
            ),
        )
        super(AdminOptionsForm, self).__init__(*args, **kwargs)

        # Form defaults or saved values

        option = Option()
        for field in self.fields:
            self.fields[field].initial = option.get(field)

class UserAdminForm(forms.ModelForm):

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
                    Submit('submit', _('Save'), css_class='radius'),
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
            Fieldset(_('Problem description'),
                'title',
                'description',
            ),
            Fieldset(_('Criterias'),
                'criteria',
            ),
            Fieldset(_('Permissions'),
                'public',
            ),
            ButtonHolder(
                Submit('submit', _('Save'), css_class='radius'),
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
        problem = kwargs['problem']
        kwargs.pop('problem')
        self.helper = FormHelper()
        self.helper.form_action = '.'
        self.helper.layout = Layout(
            'contributor',
            'problem',
            Row(Column(
                Submit('submit', _('Save'), css_class='right radius'), css_class='large-12 top-1em',
            )),
        )
        super(ContributorForm, self).__init__(*args, **kwargs)
        self.fields['problem'].initial = problem

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
            Row(Column(HTML('<h4>' + _('Quantification') + '</h4>'), css_class='large-12')),
            Row(Column(HTML('<p class="formHint quantifier-help">' + _('Users will use 5 stars to rate how ideas match each criteria. Describe what each number of star means.') + '</p>'), css_class="large-12"))
        )
        for i in range(1,6):
            layout_args += (Row(Column(HTML('<label class="right inline">' + star * i + '</label>'), css_class='large-2'), Column(Field('help_star%d' % i), css_class='large-10')),)
        layout_args += (ButtonHolder(
            Submit('submit', _('Save'), css_class='radius'),
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

        layout_args = (
            HTML('<h3>' + _('Give your idea') + '</h3>'),
            'title',
            'content',
            HTML('<h5 class="top-1em">' + _('How this idea meet the problem criterias') + '</h5>')) \
                + criteria_html \
                + criteria_fields \
                + (HTML('<hr/>'),) \
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
                Column(Submit('submit', _('Submit'), css_class='button tiny radius'), css_class='large-2 alignright'),
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
                Submit('submit', _('Save'), css_class='radius'),
            ),
        )
        super(AlternativeForm, self).__init__(*args, **kwargs)
