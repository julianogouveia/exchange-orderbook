from django.db import models
from django.conf import settings
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from exchange_core.models import BaseModel
from model_utils.models import TimeStampedModel


"""
" O gateway serve para gerar as novas carteiras para a moeda X dentro do sistema,
" servindo também para o pagamento das solicitações de saque da mesma moeda X
"""

# Diz para o moeda X que gateway ela deverá usar
class CurrencyGateway(TimeStampedModel, BaseModel):
	currency = models.ForeignKey('exchange_core.Currencies', related_name='gateway', on_delete=models.CASCADE)
	gateway = models.CharField(max_length=50, choices=settings.SUPPORTED_PAYMENT_GATEWAYS)

	def __str__(self):
		return self.currency.name

	class Meta:
		verbose_name = _("Currency Gateway")
		verbose_name_plural = _("Currencies Gateway")


@admin.register(CurrencyGateway)
class CurrencyGatewayAdmin(admin.ModelAdmin):
	list_display = ('currency', 'symbol', 'gateway')

	def symbol(self, o):
		return o.currency.symbol

	def has_add_permission(self, request):
		return False

	def has_delete_permission(self, *args, **kwargs):
		return False