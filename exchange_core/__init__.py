from decimal import Decimal
from json import JSONEncoder
from uuid import UUID

from django.conf import settings


# Reescreve o enconder Json padrão para suportar Decimal e UUID
JSONEncoder_default = JSONEncoder.default

def JSONEncoder_new(self, o):
    if isinstance(o, UUID): return str(o)
    if isinstance(o, Decimal): return round(float(o), 8)
    return JSONEncoder_olddefault(self, o)

JSONEncoder.default = JSONEncoder_new

# Define o nome do modulo
PACKAGE_NAME = 'exchange_core'

# Diz ao Django aonde está a configuração desse modulo
default_app_config = PACKAGE_NAME + '.apps.Config'

# Adiciona https://github.com/Bouke/django-two-factor-auth
# Adiciona https://github.com/django-extensions/django-extensions
# Adiciona https://github.com/jazzband/django-widget-tweaks
settings.INSTALLED_APPS += [
	'django_otp',
    'django_otp.plugins.otp_static',
    'django_otp.plugins.otp_totp',
    'two_factor',
    'django_extensions',
    'widget_tweaks'
]

# Adiciona os middlewares do Two Factor para habilitar a autenticação em dois passos
settings.MIDDLEWARE += [
	'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
]

# Define a model do usuário como sendo a model Users desse modulo
settings.AUTH_USER_MODEL = PACKAGE_NAME + '.Users'

# Define o template do Two Factor para ser usado no login
settings.LOGIN_URL = 'two_factor:login'