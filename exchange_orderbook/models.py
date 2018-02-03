from decimal import Decimal

from django.db import models
from django.conf import settings
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from exchange_core.models import BaseModel
from model_utils import Choices
from model_utils.models import TimeStampedModel

class BaseCurrencies(TimeStampedModel, BaseModel):
	currency = models.OneToOneField('exchange_core.Currencies', related_name='base_currencies', on_delete=models.CASCADE)

	def __str__(self):
		return self.currency.name

	class Meta:
		verbose_name = _("Base Currency")
		verbose_name_plural = _("Base Currencies")


class Markets(TimeStampedModel, BaseModel):
	base_currency = models.ForeignKey(BaseCurrencies, related_name='markets', on_delete=models.CASCADE)
	currency = models.ForeignKey('exchange_core.Currencies', related_name='markets', on_delete=models.CASCADE)
	min_price = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00'))
	max_price = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00'))

	class Meta:
		verbose_name = _("Market")
		verbose_name_plural = _("Markets")


class Orders(TimeStampedModel, BaseModel):
	# B for buy
	# S for sell
	TYPES = Choices('b', 's')
	STATUS = Choices('created', 'executed')

	market = models.ForeignKey(Markets, related_name='orders', on_delete=models.CASCADE)
	user = models.ForeignKey('exchange_core.Users', related_name='orders', on_delete=models.CASCADE)
	price = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00'))
	unit = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00'))
	amount = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00'))
	type = models.CharField(max_length=1, choices=TYPES)
	status = models.CharField(max_length=1, choices=STATUS, default=STATUS.created)


@admin.register(BaseCurrencies)
class BaseCurrenciesAdmin(admin.ModelAdmin):
    list_display = ('currency',)


@admin.register(Markets)
class MarketsAdmin(admin.ModelAdmin):
    list_display = ('base_currency', 'currency', 'min_price', 'max_price',)