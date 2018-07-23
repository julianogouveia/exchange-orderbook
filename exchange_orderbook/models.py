from decimal import Decimal

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from model_utils import Choices
from model_utils.models import TimeStampedModel

from exchange_core.models import BaseModel


class BaseCurrencies(TimeStampedModel, BaseModel):
    currency = models.OneToOneField('exchange_core.Currencies', related_name='base_currencies',
                                    on_delete=models.CASCADE)
    order = models.IntegerField(default=100)

    def __str__(self):
        return self.currency.name

    class Meta:
        verbose_name = _("Base Currency")
        verbose_name_plural = _("Base Currencies")


class Markets(TimeStampedModel, BaseModel):
    base_currency = models.ForeignKey(BaseCurrencies, related_name='markets', on_delete=models.CASCADE)
    currency = models.ForeignKey('exchange_core.Currencies', related_name='markets', on_delete=models.CASCADE)
    min_price = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00'))
    max_price = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('1000000.00'))

    class Meta:
        verbose_name = _("Market")
        verbose_name_plural = _("Markets")


class Orders(TimeStampedModel, BaseModel):
    # B for buy
    # S for sell
    TYPES = Choices('b', 's')
    STATUS = Choices('created', 'executed', 'canceled')

    market = models.ForeignKey(Markets, related_name='orders', on_delete=models.CASCADE)
    user = models.ForeignKey('exchange_core.Users', related_name='orders', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00'))
    amount = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00'))
    type = models.CharField(max_length=1, choices=TYPES)
    status = models.CharField(max_length=30, choices=STATUS, default=STATUS.created)

    def __str__(self):
        return '{} | {} | {} - {} | {} - {}'.format(self.user.username, self.type, self.price, 
                                                    self.market.base_currency.currency.symbol, 
                                                    self.amount, self.market.currency.symbol)

    @property
    def total(self):
        return self.price * self.amount

    @property
    def type_name(self):
        if self.type == self.TYPES.b:
            return _("Buy")
        if self.type == self.TYPES.s:
            return _("Sell")

    class Meta:
        verbose_name = ("Order")
        verbose_name_plural = ("Orders")

class Earnings(TimeStampedModel, BaseModel):
    active_order = models.OneToOneField(Orders, related_name='active_orders', on_delete=models.CASCADE)
    passive_order = models.OneToOneField(Orders, related_name='passive_orders', on_delete=models.CASCADE)
    active_fee = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00'))
    passive_fee = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00'))


class OHLC(BaseModel):
    market = models.ForeignKey(Markets, related_name='ohlc', on_delete=models.CASCADE)
    timestamp = models.DateField()
    open = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00'))
    high = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00'))
    low = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00'))
    close = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00'))
