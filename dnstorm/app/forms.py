import re
import json

from django import forms
from django.http import Http404
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from dnstorm.settings import LANGUAGES
from dnstorm.app.models import Option, Problem, Idea, Comment, \
    Criteria, Message, Quantifier, QuantifierValue, QUANTIFIER_CHOICES

from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import Fieldset, Field, \
    Row, HTML, ButtonHolder, Submit, Layout, Column

from dnstorm.app.lib.slug import unique_slugify

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
    criteria = forms.Field(_('Criterias'))
    quantifier_format = forms.ChoiceField(label='', choices=QUANTIFIER_CHOICES, widget=forms.Select(), initial='', required=False)
    notice = forms.BooleanField(_('Mail an update notice to participants'))
    invite = forms.Field(_('Invite people to participate'))

    class Meta:
        model = Problem

    def quantifier_row(self, keys):
        return '''
            <div class="row quantifier-entry">
                <div class="columns large-2"><a href="javascript:void(0)" class="button secondary tiny radius">%(format)s</a></div>
                <div class="columns large-3"><input name="quantifiername_%(id)d_%(format)s" type="text" value="%(name)s" placeholder="%(name_placeholder)s" /></div>
                <div class="columns large-5"><textarea name="quantifierhelp_%(id)d_%(format)s" placeholder="%(help_placeholder)s">%(help)s</textarea></div>
                <div class="columns large-2"><a href="javascript:void(0)" class="button alert tiny radius quantifier-remove-dialog"><i class="foundicon-minus"></i>&nbsp;%(remove)s</a></div>
            </div>''' % keys

    def quantifier_rows(self):
        if not self.instance:
            return False
        html = ''
        for q in Quantifier.objects.filter(problem=self.instance):
            format = [qt[1] for qt in QUANTIFIER_CHOICES if qt[0] == q.format]
            format = unicode(format[0]) if len(format) > 0 else False
            if not format:
                continue
            html += self.quantifier_row({
                'id': q.id,
                'format': q.format,
                'name': q.name,
                'help': q.help,
                'name_placeholder': _('Quantifier name'),
                'help_placeholder': _('Help text'),
                'remove': _('Remove')
            })
        return html

    def __init__(self, *args, **kwargs):
        self.instance = kwargs['instance'] if 'instance' in kwargs else False
        self.helper = FormHelper()
        self.helper.form_action = '.'
        self.helper.form_class = 'problem-form'
        self.helper.layout = Layout(
            Fieldset(_('Problem description'),
                'title',
                'description',
                Field('criteria', css_class='problem-criteria', template='field_criteria.html'),
            ),
            Fieldset(_('Idea Quantifiers'),
                Row(
                    Column(Field('quantifier_format'), css_class="large-9"),
                    Column(HTML('<a href="javascript:void(0)" id="quantifier-add" class="button small radius"><i class="foundicon-plus"></i>&nbsp;' + _('Add quantifier') + '</a>'), css_class="large-3"),
                ),
                HTML('<div id="quantifiers">' + self.quantifier_rows() + '</div>'),
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
        if instance:
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
        self.fields['parent'].required = False

class IdeaForm(forms.ModelForm):

    class Meta:
        model = Idea

    class Media:
        css = {'all':(
            'dnstorm/css/foundation-datepicker.css',
        )}

    def __init__(self, *args, **kwargs):

        if 'problem' in kwargs:
            problem = kwargs['problem']
            del kwargs['problem']
        elif 'instance' in kwargs:
            problem = kwargs['instance'].problem
        else:
            raise Http404

        # Quantifiers

        quantifiers = problem.quantifier_set.all()
        layout_args = ['title', 'content']
        extra_fields = dict()

        # Set quantifier fields
        for q in quantifiers:
            q_key = 'quantifier_' + str(q.id) + '_' + q.format
            if q.format == 'text':
                extra_fields[q_key] = forms.CharField(label=q.name, required=True, help_text=q.help)
            elif q.format == 'number':
                extra_fields[q_key] = forms.IntegerField(label=q.name, required=True, help_text=q.help)
            elif q.format == 'boolean':
                extra_fields[q_key] = forms.BooleanField(label=q.name, required=False, help_text=q.help)
            elif q.format == 'daterange':
                extra_fields[q_key + '_01'] = forms.DateField(label=q.name, required=True, help_text=q.help)
                extra_fields[q_key + '_02'] = forms.DateField(label='&nbsp;', required=True, help_text='&nbsp;')
            else:
                continue

        # Insert fields in layout
        for q in quantifiers:
            q_key = 'quantifier_' + str(q.id) + '_' + q.format
            if q.format == 'daterange':
                layout_args.append(Row(
                    Column(q_key + '_01', css_class='large-6'),
                    Column(q_key + '_02', css_class='large-6')),)
            else:
                layout_args.append(q_key)
        layout_args += (Submit('submit', _('Submit'), css_class='right radius'),)

        # Form instantiation
        self.helper = FormHelper()
        self.helper.form_action = '.'
        self.helper.layout = Layout(*layout_args)
        super(IdeaForm, self).__init__(*args, **kwargs)
        self.fields['content'].label = ''
        self.fields = dict(self.fields.items() + extra_fields.items())

        # Set initial data
        if self.instance.id:
            for q in quantifiers:
                if q.format == 'daterange':
                    continue
                q_key = 'quantifier_' + str(q.id) + '_' + q.format
                try:
                    qv = QuantifierValue.objects.get(quantifier=q.id, idea=self.instance).value
                except QuantifierValue.DoesNotExist:
                    qv = ''
                extra_fields[q_key].initial = qv
            for q in quantifiers:
                if q.format != 'daterange':
                    continue
                q_keys = [
                    'quantifier_' + str(q.id) + '_' + q.format + '_01',
                    'quantifier_' + str(q.id) + '_' + q.format + '_02'
                ]
                try:
                    qv = QuantifierValue.objects.get(quantifier=q.id, idea=self.instance).value
                    qv = json.loads(qv) if len(qv) > 0 else ['', '']
                except QuantifierValue.DoesNotExist:
                    qv = ['', '']
                extra_fields[q_keys[0]].initial = qv[0]
                extra_fields[q_keys[1]].initial = qv[1]

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
        model = Comment

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
