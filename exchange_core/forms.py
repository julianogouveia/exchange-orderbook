from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django import forms
from django.core.files import File
from passwords.fields import PasswordField

import account.forms

from .models import Users


class SignupForm(account.forms.SignupForm):
    first_name = forms.CharField()
    last_name = forms.CharField()
    password = PasswordField(label=_("Password"), strip=settings.ACCOUNT_PASSWORD_STRIP)
    
    field_order = ['first_name', 'last_name', 'username', 'email', 'password', 'password_confirm', 'code']


class ResetTokenForm(account.forms.PasswordResetTokenForm):
    password = PasswordField(label=_("Password"), strip=settings.ACCOUNT_PASSWORD_STRIP)


class AccountSettingsForm(account.forms.SettingsForm):
    pass


class AvatarForm(forms.ModelForm):
    class Meta:
        model = Users
        fields = ('avatar',)