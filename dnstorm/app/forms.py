import re
import json

from django import forms
from django.http import Http404
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.template.loader import render_to_string

from dnstorm.settings import LANGUAGES
from dnstorm.app import models
from dnstorm.app.lib.get import get_object_or_none

from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import *

from ajax_select.fields import AutoCompleteSelectMultipleField
from ajax_select import make_ajax_field

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
    contributor = AutoCompleteSelectMultipleField('user', required=False)
    manager = AutoCompleteSelectMultipleField('user', required=False)

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
                'contributor',
                'manager',
            ),
            ButtonHolder(
                Submit('submit', _('Save'), css_class='radius'),
            ),
        )
        super(ProblemForm, self).__init__(*args, **kwargs)

        if self.instance.id:
            self.fields['criteria'].initial = [c.id for c in self.instance.criteria.all()]

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

    class Meta:
        model = models.Idea

    def __init__(self, *args, **kwargs):

        if 'problem' in kwargs:
            idea = None
            problem = kwargs['problem']
            del kwargs['problem']
        elif 'instance' in kwargs:
            idea = kwargs['instance']
            problem = idea.problem
        else:
            raise Http404

        super(IdeaForm, self).__init__(*args, **kwargs)

        # Add criterias

        criteria_html = tuple()
        criteria_fields = tuple()
        context = dict()
        for c in problem.criteria.all():
            context['criteria'] = c
            s = get_object_or_none(models.IdeaCriteria, idea=idea, criteria=c)
            context['stars'] = s.stars if s else 0
            criteria_html += (HTML(render_to_string('criteria_vote.html', context)),)
            self.fields['criteria_%d' % c.id] = forms.IntegerField(label=c.name, initial=context['stars'])
            criteria_fields += (Field('criteria_%d' % c.id, type='hidden'),)

        errors = ''
        if re.match(r'.*criteria_.*', str(self.errors)):
            errors = HTML('<small class="error">' + _('All quantifiers are needed to submit an idea.') + '</small>')

        layout_args = (
            HTML('<h3>' + _('Describe the idea') + '</h3>'),
            'title',
            'content',
            HTML('<h3 class="top-1em">' + _('How this idea meet the problem criterias') + '</h3>'), errors) + criteria_html + criteria_fields + (HTML('<hr/>'),) + (Submit('submit', _('Submit'), css_class='right radius'),)

        # Form instantiation
        self.helper = FormHelper()
        self.helper.form_action = '.'
        self.helper.layout = Layout(*layout_args)

    def clean(self):
        date_re = re.compile('quantifier_(?P<id>[0-9]+)_daterange_(01|02)')
        date_ids = list(set([date_re.match(f).group('id') for f in self.fields if date_re.match(f)]))
        for id in date_ids:
            key = 'quantifier_' + id + '_daterange_'
            if key + '01' not in self.cleaned_data or key + '02' not in self.cleaned_data:
                raise forms.ValidationError(_('You need to provide the date fields.'))
            if self.cleaned_data[key + '01'] > self.cleaned_data[key + '02']:
                raise forms.ValidationError(_('The initial date is bigger than the end date.'))
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

class MessageForm(forms.ModelForm):
    subject = forms.CharField(label=_('Subject'), widget=forms.TextInput)

    class Meta:
        model = models.Message
        exclude = ['problem', 'sender']

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_action = '.'
        self.helper.layout = Layout(
            Fieldset(_('Send message'),
                'subject',
                'content',
                ButtonHolder(Submit('submit', _('Send message')), css_class='alignright'),
            )
        )
        super(MessageForm, self).__init__(*args, **kwargs)
        self.fields['subject'].help_text = _('The subject of the mail message to be sent.')
        self.fields['content'].help_text = _('This message will be sent in plain text to everyone envolved with this problem (managers, invited users, idea contributors and commenters).')

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
