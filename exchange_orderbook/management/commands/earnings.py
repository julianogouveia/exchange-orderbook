from django.db import transaction

from django.core.management.base import BaseCommand
from exchange_orderbook.models import Earnings, Orders

class Command(BaseCommand):
    help = 'Shows the orderbook earnings'

    def handle(self, *args, **options):
        reporting = {}

        for earning in Earnings.objects.select_related('active_order__market__base_currency__currency', 'active_order__market__currency', 'passive_order__market__base_currency__currency', 'passive_order__market__currency').iterator():
            if earning.active_order.type == Orders.TYPES.b:
                if earning.active_order.market.base_currency.currency.symbol in reporting:
                    reporting[earning.active_order.market.base_currency.currency.symbol] += earning.active_fee
                else:
                    reporting[earning.active_order.market.base_currency.currency.symbol] = earning.active_fee
            elif earning.active_order.type == Orders.TYPES.s:
                if earning.active_order.market.currency.symbol in reporting:
                    reporting[earning.active_order.market.currency.symbol] += earning.active_fee
                else:
                    reporting[earning.active_order.market.currency.symbol] = earning.active_fee

            if earning.passive_order.type == Orders.TYPES.b:
                if earning.passive_order.market.base_currency.currency.symbol in reporting:
                    reporting[earning.passive_order.market.base_currency.currency.symbol] += earning.passive_fee
                else:
                    reporting[earning.passive_order.market.base_currency.currency.symbol] = earning.passive_fee
            elif earning.passive_order.type == Orders.TYPES.s:
                if earning.passive_order.market.currency.symbol in reporting:
                    reporting[earning.passive_order.market.currency.symbol] += earning.passive_fee
                else:
                    reporting[earning.passive_order.market.currency.symbol] = earning.passive_fee

        print(reporting)