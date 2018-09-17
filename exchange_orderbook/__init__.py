from decimal import Decimal

from django.conf import settings
from prettyconf.configuration import Configuration

# Tells to prettyconf the .env path
config = Configuration(starting_path=settings.BASE_DIR)

# Defines the exchange_orderbook package name
PACKAGE_NAME = 'exchange_orderbook'

# Tells to django where is the configuration class of this package
default_app_config = PACKAGE_NAME + '.apps.Config'

# Orderbook session config
settings.ORDERBOOK_BASE_CURRENCY_SESSION_NAME = config('ORDERBOOK_BASE_CURRENCY_SESSION_NAME', default='orderbook_base_currency')
settings.ORDERBOOK_MARKET_SESSION_NAME = config('ORDERBOOK_MARKET_SESSION_NAME', default='orderbook_market')
settings.INTERMEDIATION_PASSIVE_FEE = config('INTERMEDIATION_PASSIVE_FEE', default=Decimal('0.003'), cast=Decimal)
settings.INTERMEDIATION_ACTIVE_FEE = config('INTERMEDIATION_ACTIVE_FEE', default=Decimal('0.005'), cast=Decimal)

# Orders listing config
settings.ORDERBOOK_TABLE_LIMIT = config('ORDERBOOK_TABLE_LIMIT', default=50)
settings.STOCK_CHART_THEME = config('STOCK_CHART_THEME', default='light')
settings.STOCK_CHART_HEIGHT = config('STOCK_CHART_HEIGHT', default=400, cast=int)

#
settings.ALLOW_SAME_USER_ORDER_MATCH = config('ALLOW_SAME_USER_ORDER_MATCH', default=False, cast=config.boolean)

# Adds the context for project configuration
settings.TEMPLATES[0]['OPTIONS']['context_processors'] += [
    PACKAGE_NAME + '.context_processors.exchange',
]
