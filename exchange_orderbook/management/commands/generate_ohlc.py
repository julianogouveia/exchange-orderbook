from datetime import timedelta
from django.db import transaction
from django.utils import timezone

from django.core.management.base import BaseCommand
from exchange_orderbook.models import OHLC, CurrencyPairs, Orders

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)


class Command(BaseCommand):
    help = 'Generate the OHLC table for stocks chart'        

    def handle(self, *args, **options):
        while True:
            markets = CurrencyPairs.objects.all()

            for market in markets:
                orders = Orders.objects.filter(status=Orders.STATUS.executed, modified__date__lt=timezone.now(), market=market, type=Orders.TYPES.s).order_by('created')

                if not orders.exists():
                    continue

                start_date = orders.first().created.date()
                end_date = (timezone.now() - timedelta(1)).date()

                with transaction.atomic():
                    for date in daterange(start_date, end_date):
                        date_orders = Orders.objects.filter(status=Orders.STATUS.executed, modified__date=date, market=market, type=Orders.TYPES.s)

                        if OHLC.objects.filter(timestamp=date, market=market).exists():
                            print('Record already exists for date {}'.format(date))
                            continue

                        ohlc = OHLC()
                        ohlc.timestamp = date
                        ohlc.open = getattr(date_orders.first(), 'price', None) or 0
                        ohlc.high = getattr(date_orders.order_by('-price').first(), 'price', None) or 0
                        ohlc.low = getattr(date_orders.order_by('price').first(), 'price', None) or 0
                        ohlc.close = getattr(date_orders.last(), 'price', None) or 0
                        ohlc.market = market
                        ohlc.save()

                        print(ohlc.open, ohlc.high, ohlc.low, ohlc.close)
                        print('Recording OHLC for date {}'.format(date))
