import uuid
from decimal import Decimal

from django.db import models, transaction
from django.db.models.signals import post_save
from django.contrib import admin
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel, StatusModel
from model_utils import Choices


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


class Users(TimeStampedModel, AbstractUser, BaseModel):
    STATUS = Choices('created')

    sponsor = models.ForeignKey('self', null=True, blank=True, verbose_name=_("Sponsor"), on_delete=models.CASCADE)
    status = models.CharField(max_length=30, default=STATUS.created, verbose_name=_("Status"))

    objects = UserManager()

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")


class Currencies(TimeStampedModel, BaseModel):
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10)
    icon = models.ImageField(null=True, blank=True, verbose_name=_("Icon"))

    class Meta:
        verbose_name = 'Currency'
        verbose_name_plural = 'Currencies'
        ordering = ['name']

    def __str__(self):
        return self.name


class Accounts(TimeStampedModel, BaseModel):
    currency = models.ForeignKey(Currencies, related_name='accounts', verbose_name=_("Currency"), on_delete=models.CASCADE)
    user = models.ForeignKey(Users, related_name='accounts', null=True, verbose_name=_("User"), on_delete=models.CASCADE)
    deposit = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00'))
    reserved = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00'))
    deposit_address = models.CharField(max_length=255, null=True, blank=True)
    withdraw_address = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = 'Currency Account'
        verbose_name_plural = 'Currencies Accounts'
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
        currencies = Currencies.objects.all()
        
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
        users = Users.objects.exclude(accounts__currency=instance)

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