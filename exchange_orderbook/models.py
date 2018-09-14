from decimal import Decimal

from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel

from exchange_core.models import BaseModel
from exchange_orderbook.choices import SIDE_CHOICES, STATE_CHOICES, CREATED_STATE


class BaseCurrencies(TimeStampedModel, BaseModel):
    currency = models.OneToOneField('exchange_core.Currencies', related_name='base_currencies', on_delete=models.CASCADE)
    order = models.IntegerField(default=100)

    def __str__(self):
        return self.currency.name

    class Meta:
        verbose_name = _("Currency Pair")
        verbose_name_plural = _("Currency Pairs")


class CurrencyPairs(TimeStampedModel, BaseModel):
    base_currency = models.ForeignKey(BaseCurrencies, related_name='currency_pairs', on_delete=models.CASCADE)
    quote_currency = models.ForeignKey('exchange_core.Currencies', related_name='currency_pairs', on_delete=models.CASCADE)
    min_price = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00'))
    max_price = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('1000000.00'))

    def __str__(self):
        return '{}/{}'.format(self.base_currency.currency.code, self.quote_currency.code)

    class Meta:
        verbose_name = _("Pair")
        verbose_name_plural = _("Pairs")


class Orders(TimeStampedModel, BaseModel):
    currency_pair = models.ForeignKey(CurrencyPairs, related_name='orders', on_delete=models.CASCADE, verbose_name=_("Currency Pair"))
    user = models.ForeignKey('exchange_core.Users', related_name='orders', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00'))
    amount = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00'))
    fee = models.DecimalField(max_digits=20, decimal_places=8, null=True)
    fee_currency = models.ForeignKey('exchange_core.Currencies', related_name='orders', on_delete=models.CASCADE, null=True)
    side = models.CharField(max_length=1, choices=SIDE_CHOICES)
    state = models.CharField(max_length=30, choices=STATE_CHOICES, default=CREATED_STATE)
    executed_at = models.DateTimeField(null=True)

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
        ordering = ['-created']

    def __str__(self):
        return '{} | {} - {} | {} - {}'.format(self.side, self.price,
                                               self.currency_pair.base_currency.currency.code,
                                               self.amount, self.currency_pair.quote_currency.code)

    @property
    def total(self):
        return self.price * self.amount


class Trades(TimeStampedModel, BaseModel):
    taker_order = models.OneToOneField(Orders, related_name='taker_orders', on_delete=models.CASCADE)
    taker_fee = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00'))
    maker_order = models.OneToOneField(Orders, related_name='maker_orders', on_delete=models.CASCADE)
    maker_fee = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00'))

    class Meta:
        verbose_name = _("Trade")
        verbose_name_plural = _("Trades")
