from django import forms
from django.utils.translation import ugettext as _

from settings import LANGUAGES

from dnstorm.models import Problem, Idea, Comment
from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import Fieldset, Field, \
    Row, HTML, ButtonHolder, Submit, Layout, Column

class RowCollapse(Row):
    css_class = 'row collapse'

class OptionsForm(forms.Form):
    site_title = forms.CharField(label=_('Site title'), initial='DNStorm')
    site_description = forms.CharField(label=_('Site description'), initial=_('An idea-generation platform'))

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_action = '.'
        self.helper.layout = Layout(
            Fieldset(u'Site',
                'site_title',
                'site_description'
            ),
            ButtonHolder(
                Submit('submit', _('Save')),
            ),
        )
        super(OptionsForm, self).__init__(*args, **kwargs)


class ProblemForm(forms.ModelForm):
    tag = forms.Field(_('Tags'), help_text=_('Type to search for tags.'))

    class Meta:
        model = Problem

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_action = '.'
        self.helper.layout = Layout(
            Fieldset(_('Problem description'),
                'title',
                'description',
                Field('tag', css_class='problem-tag', template='field_tag.html')
            ),
            Fieldset(_('Permissions'),
                'contributor',
                'manager',
                Row(
                    Column('open', css_class='large-4'),
                    Column('public', css_class='large-4'),
                    Column('max', css_class='large-4'),
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
        self.fields['tag'].required = False

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
