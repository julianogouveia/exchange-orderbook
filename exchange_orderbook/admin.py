from django.contrib import admin
from exchange_core.admin import BaseAdmin
from exchange_orderbook.models import BaseCurrencies, Markets, Earnings, Orders


@admin.register(BaseCurrencies)
class BaseCurrenciesAdmin(admin.ModelAdmin):
    list_display = ('currency',)


@admin.register(Markets)
class MarketsAdmin(admin.ModelAdmin):
    list_display = ('base_currency', 'currency', 'min_price', 'max_price',)

@admin.register(Earnings)
class EarningsAdmin(admin.ModelAdmin):
    list_display = ('active_order', 'passive_order', 'active_fee', 'passive_fee',)

@admin.register(Orders)
class OrdersAdmin(admin.ModelAdmin):
    orders = ('orders')

    class Meta:
        verbose_name = ("Order")
        verbose_name_plural = ("Orders")
    