import uuid
from decimal import Decimal

from django.db import models
from django.contrib import admin
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel, StatusModel
from model_utils import Choices


class Users(TimeStampedModel, AbstractUser):
    STATUS = Choices('created')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sponsor = models.ForeignKey('self', null=True, blank=True, verbose_name=_("Sponsor"))
    status = models.CharField(max_length=30, default=STATUS.created, verbose_name=_("Status"))

    objects = UserManager()

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")


class Currencies(TimeStampedModel, models.Model):
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10)
    icon = models.ImageField(null=True, blank=True, verbose_name=_("Icon"))

    class Meta:
        verbose_name = 'Currency'
        verbose_name_plural = 'Currencies'
        ordering = ['name']

    def __str__(self):
        return self.name


class Accounts(TimeStampedModel, models.Model):
    currency = models.ForeignKey(Currencies, related_name='accounts')
    user = models.ForeignKey('users.User', related_name='accounts', null=True)
    deposit = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00'))
    reserved = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00'))
    deposit_address = models.CharField(max_length=255, null=True, blank=True)
    withdraw_address = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'
        ordering = ['currency__name']

    def __str__(self):
        return '{} - {}'.format(self.user.username, self.currency.symbol)

    @property
    def balance(self):
        return self.deposit + self.reserved


# Cria as contas do usuário
@receiver(post_save, sender=Users, dispatch_uid='create_user_accounts')
def create_user_accounts(sender, instance, created, **kwargs):
    if created:
        with transaction.atomic():
            for currency in currencies:
                account = Accounts()
                account.user = instance
                account.currency = currency
                account.save()


@receiver(post_save, sender=Currencies, dispatch_uid='create_currency_user_accounts')
def create_currency_user_accounts(sender, instance, created, **kwargs):
    with transaction.atomic():
        # Filtra pelos usuários que ainda não tem essa conta
        users = User.objects.exclude(accounts__currency__pk=instance.pk)

        for user in users:
            account = Accounts()
            account.currency = instance
            account.user = user
            account.save()


@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    list_display = ['username', 'sponsor', 'first_name', 'last_name', 'email', 'created']
    ordering = ('-created',)
    exclude = ('groups', 'user_permissions', 'is_superuser', 'last_login', 'is_staff', 'is_active', 'date_joined',)


@admin.register(Currencies)
class CurrenciesAdmin(admin.ModelAdmin):
    list_display = ['name', 'symbol', 'icon']


@admin.register(Accounts)
class AccountsAdmin(admin.ModelAdmin):
    list_display = ['user', 'currency', 'balance', 'deposit', 'reserved']