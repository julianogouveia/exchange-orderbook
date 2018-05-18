from decimal import Decimal

from django.conf import settings
from prettyconf.configuration import Configuration

# Diz ao pretty conf o path do .env caso não existam variáveis de ambiente para a respectiva config
config = Configuration(starting_path=settings.BASE_DIR)

# Define o nome do modulo
PACKAGE_NAME = 'exchange_orderbook'

# Diz ao Django aonde está a configuração desse modulo
default_app_config = PACKAGE_NAME + '.apps.Config'

# Orderbook configuracoes de sessao
settings.ORDERBOOK_BASE_CURRENCY_SESSION_NAME = config('ORDERBOOK_BASE_CURRENCY_SESSION_NAME', default='orderbook_base_currency')
settings.ORDERBOOK_MARKET_SESSION_NAME = config('ORDERBOOK_MARKET_SESSION_NAME', default='orderbook_market')
settings.INTERMEDIATION_PASSIVE_FEE = config('ORDERBOOK_MARKET_SESSION_NAME', default=Decimal('0.003'), cast=Decimal)
settings.INTERMEDIATION_ACTIVE_FEE = config('INTERMEDIATION_ACTIVE_FEE', default=Decimal('0.005'), cast=Decimal)

# Configurações de listagem da página de orders
settings.ORDERBOOK_TABLE_LIMIT = config('ORDERBOOK_TABLE_LIMIT', default=50)
settings.STOCK_CHART_THEME = config('STOCK_CHART_THEME', default='light')

# Adiciona o contexto para as configuracoes do projeto
settings.TEMPLATES[0]['OPTIONS']['context_processors'] += [
    'account.context_processors.account',
    PACKAGE_NAME + '.context_processors.exchange',
]