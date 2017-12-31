from django.views.generic.edit import FormView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render

from . import forms
from .models import Accounts


class ForgetPasswordView(FormView):
	template_name = 'core/forget-password.html'
	form_class = forms.ForgetPasswordForm
	success_url = ''


@method_decorator([login_required], name='dispatch')
class WalletsView(TemplateView):
	template_name = 'core/wallets.html'
	fields = [
		'pk',
		'currency__icon',
		'currency__name',
		'currency__symbol',
		'deposit',
		'reserved'
	]

	def get(self, request):
		wallets = Accounts.objects.filter(user=request.user).values(*self.fields)
		return render(request, self.template_name, {'wallets': list(wallets)})