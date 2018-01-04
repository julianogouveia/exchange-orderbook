from urllib.parse import urlencode
from django.conf import settings

import hmac
import hashlib
import requests


API_URL = 'https://www.coinpayments.net/api.php'
API_VERSION = 1
API_REQUEST_FORMAT = 'json'
API_PUBLIC_KEY = settings.COINPAYMENTS_PUBLIC_KEY
API_PRIVATE_KEY = settings.COINPAYMENTS_PRIVATE_KEY


def post(command, data={}, headers={}, **kwargs):
    data['cmd'] = command
    data['key'] = API_PUBLIC_KEY
    data['version'] = API_VERSION
    data['format'] = API_REQUEST_FORMAT

    encoded_data = urlencode(data)
    hmac_header = hmac.new(API_PRIVATE_KEY.encode('utf8'), encoded_data.encode('utf8'), hashlib.sha512).hexdigest()
    headers['hmac'] = hmac_header

    return requests.post(API_URL, data=data, headers=headers, **kwargs).json()


class CoinPayments:
    def create_transaction(self, buyer_email, amount, currency='BTC', currency1='BTC', currency2='BTC'):
        return post('create_transaction', data={
            'currency': currency,
            'currency1': currency1,
            'currency2': currency2,
            'buyer_email': buyer_email,
            'amount': amount
        })

    def get_transactions(self):
        return post('get_tx_ids')

    def get_transaction(self, transaction_id):
        return post('get_tx_info', data={'txid': transaction_id})

    def get_address(self, currency):
        return post('get_callback_address', data={'currency': currency})
