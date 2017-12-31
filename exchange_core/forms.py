from django import forms
from django.utils.translation import ugettext_lazy as _

from .models import Users


class ForgetPasswordForm(forms.Form):
	email = forms.EmailField(max_length=100)
	repeat_email = forms.EmailField(max_length=100)

	# Valida se os e-mails digitados são iguais
	def clean_repeat_email(self):
		email = self.cleaned_data['email']
		repeat_email = self.cleaned_data['repeat_email']

		if email != repeat_email:
			raise forms.ValidationError(_("The e-mails are not equal"))
		
		return repeat_email