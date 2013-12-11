from django import forms
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from config.settings import LANGUAGES

from app.models import Option, Problem, Idea, Comment, Criteria, Message
from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import Fieldset, Field, \
    Row, HTML, ButtonHolder, Submit, Layout, Column

from app.lib.slug import unique_slugify

class OptionsForm(forms.Form):
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
        super(OptionsForm, self).__init__(*args, **kwargs)

        # Form defaults or saved values

        option = Option()
        for field in self.fields:
            self.fields[field].initial = option.get(field)



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
    notice = forms.BooleanField(_('Mail an update notice to participants'))
    invite = forms.Field(_('Invite people to participate'))

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
                    Column('public', css_class='large-2'),
                    Column('locked', css_class='large-2'),
                    Column('blind', css_class='large-3'),
                    Column('max', css_class='large-2'),
                ),
            ),
            Fieldset(_('Voting'),
                Row(
                    Column('voting', css_class='large-4'),
                    Column('vote_count', css_class='large-4'),
                    Column('vote_author', css_class='large-4'),
                ),
            ),
            Fieldset(_('Mailing'),
                Row(
                    Column('notice', css_class='large-4'),
                    Column('invite', css_class='large-8'),
                ),
            ),
            ButtonHolder(
                HTML('<a id="advanced" class="button secondary radius">' + _('Advanced options') + '</a>'),
                Submit('submit', _('Save'), css_class='radius'),
            ),
        )
        super(ProblemForm, self).__init__(*args, **kwargs)

        self.fields['max'].label = ''

        # Format criteria field
        self.fields['criteria'].required = False
        self.fields['criteria'].help_text = mark_safe(_('Type the name of the criteria to search. Go to the <a href="%s">criterias page</a> if you want to edit them.' % reverse('criteria_list')))

        # Add criteria fields
        instance = kwargs.pop('instance')
        criteria = Criteria.objects.filter(problem=instance)
        for c in criteria:
            self.fields['criteria_{i}'.format(i=c.id)] = forms.CharField(widget = forms.HiddenInput(), initial=c.id, label=c.name, help_text=mark_safe(c.description), required=False)
            self.helper.layout.append((Field('criteria_{i}'.format(i=c.id), type='hidden', value=c.id)))

        # Notices field
        self.fields['notice'].required = False
        self.fields['notice'].help_text = _('Send a mail notice to the participants of this problem about the updates.')

        # Invites field
        self.fields['invite'].required = False
        self.fields['invite'].help_text = _('Comma-separated e-mails of users that will receive an invitation to participate in this problem.')

class CriteriaForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea(attrs={'id': 'criteria_description'}))
    parent = forms.ModelChoiceField(queryset=Criteria.objects.filter(parent=None))
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
            Row(Column('parent', css_class='large-12')),
            Row(Column('description', css_class='large-12')),
            Row(Column(Submit('submit', _('Save'), css_class='small radius right'), css_class='large-12')),
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
            'title',
            'content',
            Row(
                Column('cost', css_class='large-6'),
                Column('deadline', css_class='large-6')
            ),
            Submit('submit', _('Submit'), css_class='right radius'),
        )
        super(IdeaForm, self).__init__(*args, **kwargs)
        self.fields['content'].label = ''

class CommentForm(forms.ModelForm):
    idea = forms.IntegerField()
    problem = forms.IntegerField()
    content = forms.CharField(widget=forms.Textarea(attrs={'id': 'comment_content'}))

    class Meta:
        model = Comment

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_action = '.'
        self.helper.layout = Layout(
            Field('problem', type='hidden'),
            Field('idea', type='hidden'),
            Row(
                Column('content', css_class='large-10'),
                Column(Submit('submit', _('Submit'), css_class='button small'), css_class='large-2 alignright'),
            )
        )
        super(CommentForm, self).__init__(*args, **kwargs)
        self.fields['content'].label = ''

class MessageForm(forms.ModelForm):
    subject = forms.CharField(label=_('Subject'), widget=forms.TextInput)

    class Meta:
        model = Message
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
