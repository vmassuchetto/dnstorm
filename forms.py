from django import forms
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from settings import LANGUAGES

from dnstorm.models import Problem, Idea, Comment, Criteria
from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import Fieldset, Field, \
    Row, HTML, ButtonHolder, Submit, Layout, Column

from lib.slug import unique_slugify

class RowCollapse(Row):
    css_class = 'row collapse'

class OptionsForm(forms.Form):
    site_title = forms.CharField(label=_('Site title'), initial='DNStorm')
    site_description = forms.CharField(label=_('Site description'), initial=_('An idea-generation platform'))

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_action = '.'
        self.helper.layout = Layout(
            Fieldset(_('Site'),
                'site_title',
                'site_description'
            ),
            ButtonHolder(
                Submit('submit', _('Save')),
            ),
        )
        super(OptionsForm, self).__init__(*args, **kwargs)

class AccountCreateForm(forms.Form):
    username = forms.CharField(label=_('Username'))
    email = forms.EmailField(label=_('E-mail'))
    password = forms.CharField(label=_('Password'), widget=forms.PasswordInput)
    password_repeat = forms.CharField(label=_('Repeat password'), widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_action = '.'
        self.helper.layout = Layout(
            'username',
            'email',
            'password',
            'password_repeat',
            Submit('submit', _('Create account'), css_class='expand success'),
        )
        super(AccountCreateForm, self).__init__(*args, **kwargs)

class ProblemForm(forms.ModelForm):
    criteria = forms.Field(_('Criterias'))

    class Meta:
        model = Problem

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_action = '.'
        self.helper.form_class = 'problem-form'
        self.helper.layout = Layout(
            Fieldset(_('Problem description'),
                'title',
                'description',
                Field('criteria', css_class='problem-criteria', template='field_criteria.html')
            ),
            Fieldset(_('Permissions'),
                'contributor',
                'manager',
                Row(
                    Column('open', css_class='large-3'),
                    Column('public', css_class='large-3'),
                    Column('locked', css_class='large-3'),
                    Column('max', css_class='large-3'),
                ),
            ),
            Fieldset(_('Voting'),
                Row(
                    Column('voting', css_class='large-4'),
                    Column('vote_count', css_class='large-4'),
                    Column('vote_author', css_class='large-4'),
                ),
            ),
            ButtonHolder(
                HTML('<a id="advanced" class="button secondary">' + _('Advanced options') + '</a>'),
                Submit('submit', _('Save')),
            ),
        )
        super(ProblemForm, self).__init__(*args, **kwargs)

        # Format criteria field
        self.fields['criteria'].required = False
        self.fields['criteria'].help_text = mark_safe(_('Type the name of the criteria to search. Go to the <a href="%s">criterias page</a> if you want to edit them.' % reverse('criteria')))

        # Add criteria fields
        instance = kwargs.pop('instance')
        criteria = Criteria.objects.filter(problem=instance)
        for c in criteria:
            self.fields['criteria_{i}'.format(i=c.id)] = forms.CharField(widget = forms.HiddenInput(), initial=c.id, label=c.name, help_text=mark_safe(c.description), required=False)
            self.helper.layout.append((Field('criteria_{i}'.format(i=c.id), type='hidden', value=c.id)))

class CriteriaForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea(attrs={'id': 'criteria_description'}))
    mode = forms.CharField()

    class Meta:
        model = Criteria
        exclude = ['slug', 'order']

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_action = '.'
        self.helper.layout = Layout(
            Field('mode', type='hidden'),
            Row(Column('name', css_class='large-12')),
            Row(Column('description', css_class='large-12')),
            Row(Column(Submit('submit', _('Save'), css_class='small'), css_class='large-6 large-offset-6 alignright')),
        )
        super(CriteriaForm, self).__init__(*args, **kwargs)
        self.fields['mode'].initial = 'problem_criteria_create'

class IdeaForm(forms.ModelForm):

    class Meta:
        model = Idea

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_action = '.'
        self.helper.layout = Layout(
            Row(Column('content', css_class='large-12')),
            Row(Column(Submit('submit', _('Submit')), css_class='large-2 large-offset-10')),
        )
        super(IdeaForm, self).__init__(*args, **kwargs)
        self.fields['content'].label = ''

class CommentForm(forms.ModelForm):
    idea = forms.IntegerField()

    class Meta:
        model = Comment

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_action = '.'
        self.helper.layout = Layout(
            Field('idea', type='hidden'),
            RowCollapse(
                Column('content', css_class='large-10'),
                Column(Submit('submit', _('Submit'), css_class='button small'), css_class='large-2 alignright'),
            )
        )
        super(CommentForm, self).__init__(*args, **kwargs)
        self.fields['content'].label = ''

class TableTitleForm(forms.Form):
    problem = forms.IntegerField()
    title = forms.CharField(label=_('Title'))
    description = forms.CharField(label=_('Description'), widget=forms.Textarea)
    mode = forms.CharField()
    object = forms.CharField()

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_action = '.'
        self.helper.layout = Layout(
            'title',
            'description',
            Field('mode', type='hidden'),
            Field('object', type='hidden'),
            Field('problem', type='hidden'),
            ButtonHolder(
                Submit('submit', _('Save')),
            ),
        )
        super(TableTitleForm, self).__init__(*args, **kwargs)
