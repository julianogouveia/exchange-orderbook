from django.conf import settings
from prettyconf.configuration import Configuration

# Diz ao pretty conf o path do .env caso não existam variáveis de ambiente para a respectiva config
config = Configuration(starting_path=settings.BASE_DIR)

# Define o nome do modulo
PACKAGE_NAME = 'exchange_orderbook'

# Diz ao Django aonde está a configuração desse modulo
default_app_config = PACKAGE_NAME + '.apps.Config'

# Orderbook configuracoes
settings.ORDERBOOK_BASE_CURRENCY_SESSION_NAME = config('ORDERBOOK_BASE_CURRENCY_SESSION_NAME', default='orderbook_base_currency')