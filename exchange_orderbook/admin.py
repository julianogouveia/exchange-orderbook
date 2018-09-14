from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from exchange_core.admin import BaseAdmin
from exchange_orderbook.models import BaseCurrencies, CurrencyPairs, Trades, Orders
from exchange_orderbook.choices import ASK_SIDE


@admin.register(BaseCurrencies)
class BaseCurrenciesAdmin(admin.ModelAdmin):
    list_display = ('currency',)


@admin.register(CurrencyPairs)
class CurrencyPairsAdmin(BaseAdmin):
    list_display = ('base_currency', 'quote_currency', 'min_price', 'max_price',)


@admin.register(Trades)
class TradesAdmin(BaseAdmin):
    list_display = ('taker_order', 'maker_order', 'taker_fee', 'maker_fee',)


@admin.register(Orders)
class OrdersAdmin(BaseAdmin):
    list_display = ('user', 'currency_pair', 'get_amount', 'get_price', 'fee', 'get_side', 'state', 'executed', 'created', 'modified',)
    readonly_fields = ('currency_pair', 'user', 'side', 'state', 'executed')
    list_select_related = ('currency_pair',)

    def get_amount(self, o):
        return '{:.8f} {}'.format(o.amount, o.currency_pair.quote_currency.code)
    get_amount.short_description = _("Amount")

    def get_price(self, o):
        return '{:.8f} {}'.format(o.price, o.currency_pair.base_currency.currency.code)
    get_price.short_description = _("Price")

    def get_side(self, o):
        return _("Ask") if o.side == ASK_SIDE else _("Bid")
    get_side.short_description = _("Side")
