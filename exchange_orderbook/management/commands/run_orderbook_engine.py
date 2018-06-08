from django.core.management.base import BaseCommand
from exchange_orderbook.algorithms import FIFO


class Command(BaseCommand):
    help = 'Runs the orderbook engine'

    def handle(self, *args, **options):
        while True:
            engine = FIFO()
            engine.spawn()
