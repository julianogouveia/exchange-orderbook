import os
import urllib
import requests

from django.core.management.base import BaseCommand
from django.db import transaction
from django.core.files import File
from django.core.files.base import ContentFile
from lxml.html import html5parser

from exchange_core.models import Currencies
from exchange_payments.models import CurrencyGateway


BASE_URL = 'https://www.coinpayments.net/'
HEADERS = {
    'pragma': 'no-cache',
    'cookie': 'visid_incap_992349=v0nydGSGTHe+sACWL0y+biOaCVoAAAAAQUIPAAAAAACPHxl4/upxHOtQANNmge+c; incap_ses_298_992349=ksYvQcJd+gniSz1MCrciBMV1TloAAAAADK+MqE82r1qJBUAUlwHeiQ==',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'cache-control': 'no-cache',
    'authority': 'www.coinpayments.net',
    'referer': 'https://www.coinpayments.net/images/coins/GLD.png',
}

class Command(BaseCommand):
	help = 'Create the coinpayment supported coins based on https://www.coinpayments.net/supported-coins'

	def handle(self, *args, **options):
		path = os.path.dirname(__file__)
		page = html5parser.fromstring(open(path + '/supported_coins.html', 'r').read())

		for coin_row in page.cssselect('.w-row.tdr'):
			try:
				icon = BASE_URL + coin_row.cssselect('.coin-logo')[0].get('src')
				name = coin_row.cssselect('.coin-link')[0].text
				symbol = coin_row.cssselect('.table-data')[1].text

				# Só cadastra moedas inexistentes
				if not Currencies.objects.filter(symbol=symbol).exists():
					currency = Currencies()
					currency.name = name
					currency.symbol = symbol
					currency.save()

					# Faz o upload do icone
					response = requests.get(icon, headers=HEADERS)

					if response.status_code == 200:
						currency.icon.save(os.path.basename(icon), ContentFile(response.content), save=True)

					currency_gateway = CurrencyGateway()
					currency_gateway.currency = currency
					currency_gateway.gateway = 'coinpayments'
					currency_gateway.save()

					print('Cadastrando moeda {} -> {}'.format(name, symbol))
			except Exception as e:
				continue
