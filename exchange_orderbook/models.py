from decimal import Decimal

from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel

from exchange_core.models import BaseModel
from exchange_orderbook.choices import SIDE_CHOICES, STATE_CHOICES, CREATED_STATE, ASK_SIDE


class BaseCurrencies(TimeStampedModel, BaseModel):
    currency = models.OneToOneField('exchange_core.Currencies', related_name='base_currencies', on_delete=models.CASCADE, verbose_name=_("Currency"))
    order = models.IntegerField(default=100, verbose_name=_("Order"), help_text=_("The order who base currency must appears in Orderbook"))

    def __str__(self):
        return self.currency.name

    class Meta:
        verbose_name = _("Base currency")
        verbose_name_plural = _("Base currencies")


class CurrencyPairs(TimeStampedModel, BaseModel):
    base_currency = models.ForeignKey(BaseCurrencies, related_name='currency_pairs', on_delete=models.CASCADE, verbose_name=_("Base currency"))
    quote_currency = models.ForeignKey('exchange_core.Currencies', related_name='currency_pairs', on_delete=models.CASCADE, verbose_name=_("Quote currency"))
    min_price = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00'), verbose_name=_("Min price"))
    max_price = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('1000000.00'), verbose_name=_("Max price"))
    min_qty = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00'), verbose_name=_("Min quantity"))
    max_qty = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('1000000.00'), verbose_name=_("Max quantity"))

    def __str__(self):
        return '{}/{}'.format(self.base_currency.currency.code, self.quote_currency.code)

    class Meta:
        verbose_name = _("Currency pair")
        verbose_name_plural = _("Currency pairs")


class Orders(TimeStampedModel, BaseModel):
    currency_pair = models.ForeignKey(CurrencyPairs, related_name='orders', on_delete=models.CASCADE, verbose_name=_("Currency pair"))
    user = models.ForeignKey('exchange_core.Users', related_name='orders', on_delete=models.CASCADE, verbose_name=_("User"))
    price = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00'), verbose_name=_("Price"))
    qty = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00'), verbose_name=_("Quantity"))
    fee = models.DecimalField(max_digits=20, decimal_places=8, null=True, verbose_name=_("Fee"))
    fee_currency = models.ForeignKey('exchange_core.Currencies', related_name='orders', on_delete=models.CASCADE, null=True, verbose_name=_("Fee currency"))
    side = models.CharField(max_length=3, choices=SIDE_CHOICES, verbose_name=_("Side"))
    state = models.CharField(max_length=30, choices=STATE_CHOICES, default=CREATED_STATE, verbose_name=_("State"))
    executed = models.DateTimeField(null=True, verbose_name=_("Executed"))

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
        ordering = ['-created']

    @property
    def side_name(self):
        return _("Ask") if self.side == ASK_SIDE else _("Bid")

    def __str__(self):
        return '{} | {} - {} | {} - {}'.format(self.side, self.price,
                                               self.currency_pair.base_currency.currency.code,
                                               self.qty, self.currency_pair.quote_currency.code)

    @property
    def amount(self):
        return self.price * self.qty


class Trades(TimeStampedModel, BaseModel):
    taker_order = models.OneToOneField(Orders, related_name='taker_orders', on_delete=models.CASCADE)
    taker_fee = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00'))
    maker_order = models.OneToOneField(Orders, related_name='maker_orders', on_delete=models.CASCADE)
    maker_fee = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00'))

    class Meta:
        verbose_name = _("Trade")
        verbose_name_plural = _("Trades")
