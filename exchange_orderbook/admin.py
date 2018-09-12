from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from exchange_core.admin import BaseAdmin
from exchange_orderbook.models import BaseCurrencies, CurrencyPairs, Matchs, Orders


@admin.register(BaseCurrencies)
class BaseCurrenciesAdmin(admin.ModelAdmin):
    list_display = ('currency',)


@admin.register(CurrencyPairs)
class CurrencyPairsAdmin(BaseAdmin):
    list_display = ('base_currency', 'quote_currency', 'min_price', 'max_price',)


@admin.register(Matchs)
class MatchsAdmin(BaseAdmin):
    list_display = ('taker_order', 'maker_order', 'taker_fee', 'maker_fee',)


@admin.register(Orders)
class OrdersAdmin(BaseAdmin):
    list_display = ('user', 'currency_pair', 'get_amount', 'get_price', 'fee', 'get_type', 'state', 'executed_at', 'created', 'modified',)
    readonly_fields = ('currency_pair', 'user', 'side', 'state', 'executed_at')
    list_select_related = ('currency_pair',)

    def get_amount(self, o):
        return '{:.8f} {}'.format(o.amount, o.market.currency.symbol)
    get_amount.short_description = _("Amount")

    def get_price(self, o):
        return '{:.8f} {}'.format(o.price, o.market.base_currency.currency.symbol)
    get_price.short_description = _("Price")

    def get_type(self, o):
        return _("Ask") if o.type == Orders.SIDES.s else _("Bid")

    get_type.short_description = _("Type")
