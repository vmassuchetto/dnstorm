import json
import re
import urlparse
from itertools import izip
from decimal import Decimal

from django import forms
from django.contrib.auth.forms import UserChangeForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.validators import MinValueValidator
from django.http import Http404, QueryDict, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import *
from crispy_forms.utils import render_crispy_form
from registration.forms import RegistrationFormUniqueEmail

from dnstorm.app import models
from dnstorm.app.utils import get_object_or_none, get_option
from dnstorm.settings import LANGUAGES

class RegistrationForm(RegistrationFormUniqueEmail):
    """
    Custom registration form with the ``hash`` parameter.
    """
    hash = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        _hash = kwargs.pop('hash') if 'hash' in kwargs else None
        invitation = get_object_or_none(models.Invitation, hash=_hash) if _hash else None
        self.helper = FormHelper()
        self.helper.form_action = '%s%s' % (reverse('registration_register'), '?hash=' + _hash if _hash else '')
        self.helper.form_class = 'auth-form'
        self.helper.form_read_only = True
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
        if invitation:
            self.fields['email'].initial = invitation.user.email
            self.fields['email'].widget.attrs['readonly'] = True

    def clean_email(self, *args, **kwargs):
        """
        Validate that the supplied email address is unique for the
        site and compliant with the ``hash`` invitation parameter.
        """
        _hash = self.data['hash'] if 'hash' in self.data else ''
        if len(_hash) > 2:
            invitation = get_object_or_404(models.Invitation, hash=_hash)
            # User was invited previously and is using the same e-mail to register
            if invitation and invitation.user.email == self.cleaned_data['email']:
                return self.cleaned_data['email']
            raise forms.ValidationError(_('You need to use the same e-mail the invitation was sent.'))
        # Non-invited registration
        user = User.objects.filter(email__iexact=self.cleaned_data['email'])
        if user:
            raise forms.ValidationError(_('This email address is already in use. Please enter a different email address.'))
        return self.cleaned_data['email']

class OptionsForm(forms.Form):
    site_title = forms.CharField(label=_('Site title'), help_text=_('Page title for browser windows and e-mail subjects.'))
    site_description = forms.CharField(label=_('Site description'), help_text=_('Page description for browser windows.'))
    site_url = forms.CharField(label=_('Site URL'), help_text=_('Site domain for URL generation with http scheme. Examples: \'http://domain.com\', \'https://subdomain.domain.com\', \'http://domain:port\''))

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_action = '.'
        self.helper.layout = Layout(
            Fieldset(_('Site'),
                'site_title',
                'site_description',
                'site_url',
            ),
            ButtonHolder(
                Submit('submit', _('Save'), css_class='right radius'),
            ),
        )
        super(OptionsForm, self).__init__(*args, **kwargs)

        # Form defaults or saved values

        for field in self.fields:
            self.fields[field].initial = get_option(field)

    def clean_site_url(self):
        url = urlparse.urlparse(self.cleaned_data['site_url'])
        if not url.netloc:
            raise forms.ValidationError(_('Wrong domain format.'))
        return self.cleaned_data['site_url']

class UserForm(forms.ModelForm):
    user_id = forms.IntegerField('user_id', widget=forms.HiddenInput())

    class Meta:
        model = User

    def __init__(self, *args, **kwargs):
        try:
            request = kwargs.pop('request')
        except:
            raise Exception(_('Wrong form kwargs.'))
        super(UserForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        layout_args = ('email', 'first_name')
        if request.user.is_superuser:
            layout_args += ('is_superuser',)
        layout_args += (
            'user_id',
            Row(Column(
                ButtonHolder(
                    Submit('submit', _('Save'), css_class='right radius left-1em'),
                    HTML('<a class="button secondary radius right" href="%s"><i class="fi-key"></i>&nbsp;%s</a>' % (reverse('user_password_update', kwargs={'username': self.instance.username}), _('Change password'))),
                ),
            ), css_class='large-12 top-1em'),
        )
        self.helper.layout = Layout(*layout_args)
        self.fields['email'].required = True
        self.fields['first_name'].label = _('Display name')
        self.fields['user_id'].initial = self.instance.id
        for f in ['username', 'password', 'last_login', 'date_joined']:
            self.fields[f].required = False

class UserPasswordForm(forms.Form):
    password = forms.CharField(label=_('Type your current password'), widget=forms.PasswordInput)
    password1 = forms.CharField(label=_('Type your new password'), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_('Type your new password again.'), widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super(UserPasswordForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset('<i class="fi-torso"></i>&nbsp;' + _('Change password'),
                'password',
                'password1',
                'password2',
                ButtonHolder(
                    Submit('submit', _('Save'), css_class='right radius'),
                ),
            )
        )

    def clean(self):
        if not 'password1' or not 'password2' in self.cleaned_data or \
            self.cleaned_data['password1'] != self.cleaned_data['password2']:
            raise forms.ValidationError(_('Passwords don\'t match.'))

class CriteriaForm(forms.ModelForm):

    class Meta:
        model = models.Criteria
        exclude = ['author', 'slug', 'problem']

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_action = '.'
        self.helper.layout = Layout(
            Fieldset('<i class="fi-cloud"></i>&nbsp;' + _('Information'),
                Row(Column('name','description')),
            ),
            Fieldset('<i class="fi-"></i>&nbsp;' + _('Values'),
                Row(Column('fmt')),
                Row(
                    Column('min', css_class='large-6 minmax'),
                    Column('max', css_class='large-6 minmax')),
                Row(
                    Column('order', css_class='large-4'),
                    Column('weight', css_class='large-4'),
                    Column('result', css_class='large-4')), css_class='criteria-values'),
                Row(Column(
                    ButtonHolder(
                        Submit('submit', _('Save'), css_class='radius'), css_class='large-12 text-right')))
        )
        super(CriteriaForm, self).__init__(*args, **kwargs)

    def clean(self):
        """
        Scale format type must have minimum and maximum specified.
        """
        super(forms.ModelForm, self).clean()
        if 'fmt' in self.cleaned_data and self.cleaned_data['fmt'] == 'scale':
            if not self.cleaned_data['min']:
                self._errors['min'] = [_('Minimum scale required for this format.')]
            if not self.cleaned_data['max']:
                self._errors['max'] = [_('Maximum scale required for this format.')]
        return self.cleaned_data

class ProblemForm(forms.ModelForm):

    class Meta:
        model = models.Problem

    def __init__(self, *args, **kwargs):
        super(ProblemForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = '.'
        self.helper.form_class = 'problem-form'
        layout_args = ('title', 'description',)
        if not self.instance.published:
            layout_args += (
                Submit('publish', _('Publish'), css_class='right radius'),
                Submit('save', _('Save as draft'), css_class='right radius secondary small'))
        else:
            layout_args += (Submit('publish', _('Save edits'), css_class='right radius'),)

        self.helper.layout = Layout(*layout_args)

class ProblemCollaboratorsForm(forms.Form):
    user_search = forms.CharField(_('Search and add collaborators'), required=False, widget=forms.TextInput(attrs={'autocomplete':'off'}))
    public = forms.BooleanField(label=_('Public'), help_text=_('In public mode anyone can view this problem. You\'ll need to manually choose the collaborators with access if you leave unchecked.'), required=False)
    open = forms.BooleanField(label=_('Open edit'), help_text=_('In open contribution mode any user will be able to edit other users contents as coauthors. Leave unchecked if you want users to only modify their own content.'), required=False)

    def __init__(self, *args, **kwargs):
        self.problem = kwargs.pop('problem')
        users_html = ''.join([render_to_string('item_user_collaborator.html', {'users': self.problem.collaborator.order_by('first_name')})])
        super(ProblemCollaboratorsForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset('<i class="fi-torso"></i>&nbsp;' + _('Collaborators'),
                Row(
                    Column('user_search', help_text=_('Type to search for users. Click on them to insert or remove from the selected list. Go to the sitewide user section to resend an invitation for non-confirmed users.'), css_class='large-8'),
                    Column(Button('add_user', _('Search and add collaborators'), css_class='postfix secondary', disabled=True), css_class='large-4')
                , css_class='collapse'),
                Row(Column(Div(css_class='user-search-result'),css_class='large-12'), css_class='collapse'),
                Div(HTML(users_html), css_class='large-12 collapse user-search-selected'),
            css_class='user-search'),
            Fieldset('<i class="fi-lock"></i>&nbsp;' + _('Permissions'),
                Row(
                    Column('public', css_class='large-6'),
                    Column('open', css_class='large-6')
                ),
            ),
            Row(Column(
                ButtonHolder(
                    Submit('submit', _('Save'), css_class='right radius'),
                ),
            ), css_class='large-12 collapse'),
        )
        self.fields['public'].initial = self.problem.public
        self.fields['open'].initial = self.problem.open

class IdeaForm(forms.ModelForm):
    title = forms.CharField(required=True)

    class Meta:
        model = models.Idea
        exlude = ['problem', 'author', 'coauthor']

    def __init__(self, *args, **kwargs):
        """
        Dynamic form that validates according to the format of the given
        criteria.
        """
        layout_args = ('title', 'description')
        super(IdeaForm, self).__init__(*args, **kwargs)
        kwargs['instance'].get_data()
        for c in kwargs['instance'].criteria:
            # Custom fields
            _argfields = tuple()
            if c.fmt == 'number' \
                or c.fmt == 'scale' \
                or c.fmt == 'time':
                vk = '%d__value_%s' % (c.id, c.fmt)
                self.fields[vk] = forms.IntegerField(required=True, initial=c.value, validators=[MinValueValidator(Decimal('0.00'))], help_text=_('Give an integer value higher than zero.'))
            elif c.fmt == 'currency':
                vk = '%d__value_%s' % (c.id, c.fmt)
                self.fields[vk] = forms.DecimalField(max_digits=10, decimal_places=2, required=True, initial=c.value, validators=[MinValueValidator(Decimal('0.00'))], help_text=_('Give a currency value higher than 0. Use dots to separate cents. e.g.: 1.23; 12.34 123.45; 12345.12'))
            elif c.fmt == 'boolean':
                vk = '%d__value_%s' % (c.id, c.fmt)
                self.fields[vk] = forms.BooleanField(initial=c.value, required=False, help_text=_('Mark the checkbox to represent the \'True\' value or leave unchecked for \'False\'.'))
            dk = '%d__description' % c.id
            self.fields[dk] = forms.CharField(widget=forms.Textarea(attrs={'rows':3}), required=True, initial=c.description, help_text=_('Describe why you gave the above value for this criteria in this idea.'))

            _argfields += (vk,dk)
            _kwargfields = {'css_class': 'large-6'}

            layout_args += (
                HTML('<hr/>'),
                Row(
                    Column(HTML(render_to_string('item_criteria.html', {
                        'criteria': c, 'show_actions': False, 'show_parameters': True,
                        'show_description': True, 'show_icons': True})), css_class='large-6'),
                    Column(*_argfields, **_kwargfields),
                )
            )

        if not self.instance.published:
            layout_args += (
                Submit('publish', _('Publish'), css_class='right radius'),
                Submit('save', _('Save as draft'), css_class='right radius secondary small'))
        else:
            layout_args += (Submit('publish', _('Save edits'), css_class='right radius'),)

        # Form instantiation

        self.helper = FormHelper()
        self.helper.form_action = '.'
        self.helper.layout = Layout(*layout_args)

class CommentForm(forms.ModelForm):
    idea = forms.IntegerField()
    problem = forms.IntegerField()
    criteria = forms.IntegerField()
    alternative = forms.IntegerField()
    content = forms.CharField(widget=forms.Textarea(attrs={'id': 'comment_content'}))

    class Meta:
        model = models.Comment

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_action = '.'
        self.helper.layout = Layout(
            Field('problem', type='hidden'),
            Field('idea', type='hidden'),
            Field('criteria', type='hidden'),
            Field('alternative', type='hidden'),
            Row(
                Column('content', css_class='large-10'),
                Column(Submit('submit', _('Submit'), css_class='button small radius expand postfix'), css_class='large-2')
                ,css_class='collapse'
            )
        )
        super(CommentForm, self).__init__(*args, **kwargs)
        self.fields['content'].label = ''

class AlternativeForm(forms.ModelForm):

    class Meta:
        model = models.Alternative

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_action = '.'
        layout_args = (
            'name',
            HTML('<h4>' + _('Select the ideas for this alternative') + '</h4>'))
        current_ideas = kwargs['instance'].idea.all()
        for i in kwargs.get('instance', None).problem.idea_set.filter(published=True):
            i.get_data()
            layout_args += (Row(
                Column(HTML(render_to_string('item_idea.html', {
                    'idea': i, 'show_check': True, 'show_likes': False, 'show_actions': False,
                    'show_comments': False, 'checked': i in current_ideas})),
                    css_class='large-12'), css_class='collapse'),)
        for i in current_ideas:
            layout_args += (HTML('<input type="hidden" id="idea-' + str(i.id) + '" name="idea" value="' + str(i.id) + '" />'),)
        layout_args += (Submit('save', _('Save'), css_class='right radius'),)
        self.helper.layout = Layout(*layout_args)
        super(AlternativeForm, self).__init__(*args, **kwargs)
