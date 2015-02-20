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
from django.http import Http404, QueryDict
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
        _hash = self.data['hash'] if 'hash' in self.data else None
        if _hash:
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
        self.helper.layout = Layout(
            Fieldset('<i class="fi-torso"></i>&nbsp;' + _('Edit user \'%s\'' % self.instance.username),
                'email',
                'first_name',
                'is_superuser' if request.user.is_superuser else '',
                'user_id',
                Row(Column(
                    ButtonHolder(
                        Submit('submit', _('Save'), css_class='right radius left-1em'),
                        HTML('<a class="button secondary radius right" href="%s"><i class="fi-key"></i>&nbsp;%s</a>' % (reverse('user_password_update', kwargs={'username': self.instance.username}), _('Change password'))),
                    ),
                ), css_class='large-12 top-1em'),
            )
        )
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
    id = forms.IntegerField(widget=forms.HiddenInput, initial=0)
    criteria_description = forms.CharField(widget=forms.Textarea(attrs={'id': 'criteria_description'}))

    class Meta:
        model = models.Criteria
        exclude = ['slug', 'problem']

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.disable_csrf = True
        self.helper.form_tag = False
        self.helper.form_action = '.'
        layout_args = (
            'id',
            'name',
            'criteria_description',
            'fmt',
            Row(
                Column('min', css_class='large-6'),
                Column('max', css_class='large-6')
            , css_class='minmax'),
            Row(
                Column('order', css_class='large-4'),
                Column('weight', css_class='large-4'),
                Column('result', css_class='large-4')
            )
        )
        layout_args += (Row(Column(
            ButtonHolder(
                Button('delete', _('Delete'), css_class='criteria-delete alert small radius align-top left'),
                Button('cancel', _('Cancel'), css_class='criteria-cancel secondary small radius align-top right-1em'),
                Button('submit', _('Save criteria'), css_class='radius criteria-submit'),
            ), css_class='large-12 text-right')),
        )
        self.helper.layout = Layout(*layout_args)
        super(CriteriaForm, self).__init__(*args, **kwargs)
        if self.instance:
            self.fields['criteria_description'].initial = self.instance.description

    def clean(self):
        """
        Custom form validation.
        """
        super(forms.ModelForm, self).clean()

        if 'fmt' in self.cleaned_data and self.cleaned_data['fmt'] == 'scale':
            if not self.cleaned_data['min']:
                self._errors['min'] = [u'Minimum scale required for this format.']
            if not self.cleaned_data['max']:
                self._errors['max'] = [u'Maximum scale required for this format.']

        return self.cleaned_data

class ProblemForm(forms.ModelForm):
    user_search = forms.CharField(_('Search and add contributors'), required=False, widget=forms.TextInput(attrs={'autocomplete':'off'}))

    class Meta:
        model = models.Problem

    def __init__(self, *args, **kwargs):
        problem_perm_edit = kwargs.pop('problem_perm_edit') if 'problem_perm_edit' in kwargs else False
        problem_perm_manage = kwargs.pop('problem_perm_manage') if 'problem_perm_manage' in kwargs else False
        self.instance = kwargs['instance'] if 'instance' in kwargs and kwargs['instance'] else False
        if self.instance:
            self.instance.id = self.instance.id if hasattr(self.instance, 'id') else 0
        else:
            problem_perm_manage = True
        self.helper = FormHelper()
        self.helper.form_action = '.'
        self.helper.form_class = 'problem-form'

        layout_args = (
            Fieldset('<i class="fi-puzzle"></i>&nbsp;' + _('Problem description'),
                'title',
                'description',
            ),)

        criteria_html = ''
        if self.instance:
            for c in self.instance.criteria_set.all().order_by('name'):
                criteria_form = CriteriaForm(instance=c)
                c.fill_data()
                criteria_html += render_to_string('item_criteria.html', {'criteria': c, 'show_actions': True, 'criteria_form': criteria_form})
        criteria_html = '<div class="criteria">%s</div>' % criteria_html

        layout_args += (
            Fieldset('<i class="fi-target-two"></i>&nbsp;' + _('Criterias'),
                HTML(criteria_html),
                HTML('<a class="secondary button expand radius criteria-add">' + _('Add criteria') + '</a>'),
            ),
        )

        if self.instance and problem_perm_manage:
            layout_args += (
                Fieldset('<i class="fi-lock"></i>&nbsp;' + _('Permissions'),
                    Row(
                        Column('public', css_class='large-6'),
                        Column('open', css_class='large-6')
                    ),
                    HTML('<div class="row collapse contributors-section"><div class="columns large-12"><h5>%s</h5><p class="help">%s</p>' % (_('Contributors'), _('Users with permission to contribute to this problem. Click a user box to remove from the selection.'))),
                    HTML(render_to_string('_update_problem_users.html', {'users': self.instance.contributor.all()})),
                    Row(
                        Column('user_search', css_class='large-8'),
                        Column(Button('add_user', _('Search and add contributors'), css_class='postfix secondary', disabled=True), css_class='large-4')
                    , css_class='collapse'),
                    HTML('<div class="user-search-result"></div></div></div>'),
                ),
            )

        layout_args += (Button('delete', _('Delete problem'), css_class='left small radius alert problem-delete', data_problem=self.instance.id),)

        if not self.instance.published:
            layout_args += (
                Submit('publish', _('Publish'), css_class='right radius'),
                Submit('save', _('Save as draft'), css_class='right radius secondary small'))
        else:
            layout_args += (Submit('publish', _('Save edits'), css_class='right radius'),)

        self.helper.layout = Layout(*layout_args)
        super(ProblemForm, self).__init__(*args, **kwargs)

class DeleteForm(forms.Form):
    yes = forms.BooleanField(label=_("Yes. I know what I'm doing. Delete this!"))
    delete_problem = forms.IntegerField(widget=forms.HiddenInput())
    delete_idea = forms.IntegerField(widget=forms.HiddenInput())
    delete_comment = forms.IntegerField(widget=forms.HiddenInput())
    delete_criteria = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_action = '.'
        self.helper.form_class = 'delete-form'
        self.helper.layout = Layout(
            'delete_problem',
            'delete_idea',
            'delete_comment',
            'delete_criteria',
            Row(Column('yes', css_class='large-12')),
            Row(Column(ButtonHolder(
                HTML('<a class="button left radius secondary small close-reveal-modal-button">' + _('Cancel') + '</a>'),
                Submit('submit', _('Delete'), css_class="right radius alert")
            ), css_class='top-1em large-12'))
        )
        super(DeleteForm, self).__init__(*args, **kwargs)
        self.fields['yes'].required = True

class IdeaForm(forms.ModelForm):
    title = forms.CharField(required=True)
    problem = forms.IntegerField(widget=forms.HiddenInput())

    class Meta:
        model = models.Idea

    def __init__(self, *args, **kwargs):
        """
        Dynamic form that validates according to the format of the give
        criteria.
        """

        p = kwargs.pop('problem', None)
        layout_args = ('problem', 'title')

        super(IdeaForm, self).__init__(*args, **kwargs)
        kwargs['instance'].fill_data()

        self.fields['title'].initial = kwargs['instance'].title
        self.fields['problem'].initial = kwargs['instance'].problem

        for c in kwargs['instance'].criteria:
            # Custom fields
            _argfields = tuple()
            self.initial = dict()
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
            self.fields[dk] = forms.CharField(widget=forms.Textarea(), required=True, initial=c.description, help_text=_('Describe why you gave the above value for this criteria in this idea.'))

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

        layout_args += (Button('delete', _('Delete idea'), css_class='left small radius alert idea-delete', data_idea=self.instance.id),)

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
        self.fields['problem'].initial = p.id

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
