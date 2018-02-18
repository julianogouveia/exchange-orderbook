from django.db import transaction

from django.core.management.base import BaseCommand, CommandError
from exchange_orderbook.algorithms import FIFO

class Command(BaseCommand):
    help = 'Runs the orderbook engine'        

    def handle(self, *args, **options):
        while True:
            with transaction.atomic():
                engine = FIFO()
                engine.execute()