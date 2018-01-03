import uuid

from django.contrib.auth import get_user_model
from django.views.generic.edit import FormView
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from account.decorators import login_required
from account.models import EmailAddress
from account.hooks import hookset

import account.views

from . import forms
from .models import Users, Accounts


@method_decorator([login_required], name='dispatch')
class WalletsView(TemplateView):
    template_name = 'core/wallets.html'
    fields = [
        'pk',
        'currency__icon',
        'currency__name',
        'currency__symbol',
        'deposit',
        'reserved',
    ]

    def get(self, request):
        wallets = Accounts.objects.filter(user=request.user).values(*self.fields)
        return render(request, self.template_name, {'wallets': list(wallets)})


class SignupView(account.views.SignupView):
    form_class = forms.SignupForm

    # Sobreescreve o metodo after_signup para popular campos adicionais do usuário
    def after_signup(self, form):
        user = self.created_user
        user.first_name = form.cleaned_data['first_name']
        user.last_name = form.cleaned_data['last_name']
        user.save()


class ResetPasswordView(account.views.PasswordResetView):

    def send_email(self, email):
        User = get_user_model()
        protocol = getattr(settings, "DEFAULT_HTTP_PROTOCOL", "http")
        current_site = get_current_site(self.request)
        email_qs = EmailAddress.objects.filter(email__iexact=email)

        for user in User.objects.filter(pk__in=email_qs.values("user")):
            token = self.make_token(user)
            password_reset_url = "{0}://{1}{2}".format(
                protocol,
                current_site.domain,
                reverse("core>reset-token", kwargs=dict(uidb36=str(user.pk), token=token))
            )
            hookset.send_password_reset_email([user.email], {
                "user": user,
                "current_site": current_site,
                "password_reset_url": password_reset_url,
            })


class ResetTokenView(account.views.PasswordResetTokenView):
    form_class = forms.ResetTokenForm

    def get_user(self):
        uid_int = self.kwargs["uidb36"]
        return get_object_or_404(get_user_model(), id=uuid.UUID(uid_int))

    def form_valid(self, form):
        self.change_password(form)
        self.create_password_history(form, self.get_user())
        self.after_change_password()
        return redirect(self.get_success_url())


class AccountSettingsView(account.views.SettingsView):
    form_class = forms.AccountSettingsForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['avatar_form'] = forms.AvatarForm()
        return context