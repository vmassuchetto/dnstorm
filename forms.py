from django import forms
from django.conf.global_settings import LANGUAGES
from django.utils.translation import ugettext as _

from dnstorm.models import Problem, Idea
from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import Fieldset, Field, Row, \
    HTML, ButtonHolder, Submit, Layout, Column

class OptionsForm(forms.Form):
    language = forms.ChoiceField(label=_('Language'), choices=map(lambda (k,v): (k, _(v)), LANGUAGES), required=False)

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_action = '.'
        self.helper.layout = Layout(
            Fieldset(u'Site',
                'language',
            ),
            ButtonHolder(
                Submit('submit', _('Save')),
            ),
        )
        super(OptionsForm, self).__init__(*args, **kwargs)
        self.fields['language'].required = False


class ProblemForm(forms.ModelForm):
    tag = forms.Field(_('Tags'), help_text=_('Comma separated list of tags.'))

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
                'user',
                'manager',
                Row(
                    Column('open', css_class='large-4'),
                    Column('public', css_class='large-4'),
                    Column('max', css_class='large-4'),
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
    problem = forms.HiddenInput()

    class Meta:
        model = Idea

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_action = '.'
        self.helper.layout = Layout(
            Row(Column('content', css_class='large-12')),
            Row(Column(Submit('submit', _('Submit')), css_class='alignright'))
        )
        super(IdeaForm, self).__init__(*args, **kwargs)
        self.fields['content'].label = ''
