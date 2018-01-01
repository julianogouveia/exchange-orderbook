from decimal import Decimal
from json import JSONEncoder
from uuid import UUID

from django.conf import settings
from django.urls import reverse_lazy
from prettyconf.configuration import Configuration

# Diz ao pretty conf o path do .env caso não existam variáveis de ambiente para a respectiva config
config = Configuration(starting_path=settings.BASE_DIR)

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
# Adiciona https://github.com/pinax/django-user-accounts
# Adiciona https://github.com/anymail/django-anymail
# Adiciona https://github.com/yourlabs/django-session-security/
# O modulo django.contrib.sites é necessário para o django-user-accounts
settings.INSTALLED_APPS += [
    'django.contrib.sites', 
	'django_otp',
    'django_otp.plugins.otp_static',
    'django_otp.plugins.otp_totp',
    'two_factor',
    'django_extensions',
    'widget_tweaks',
    'account',
    'anymail',
    'session_security',
]

# Adiciona os middlewares do Two Factor para habilitar a autenticação em dois passos
settings.MIDDLEWARE += [
	'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'account.middleware.LocaleMiddleware',
    'account.middleware.TimezoneMiddleware',
    'account.middleware.ExpiredPasswordMiddleware',
    'session_security.middleware.SessionSecurityMiddleware',
]

# Define a model do usuário como sendo a model Users desse modulo
settings.AUTH_USER_MODEL = PACKAGE_NAME + '.Users'

# Define o template do Two Factor para ser usado no login
settings.LOGIN_URL = 'two_factor:login'
settings.LOGIN_REDIRECT_URL = reverse_lazy('core>wallets')

# Adiciona o contexto do pacote django-user-accounts para os templates
# Adiciona o contexto do pacote django-session-security para os templates
settings.TEMPLATES[0]['OPTIONS']['context_processors'] += [
    'account.context_processors.account',
    'django.core.context_processors.request',
]

# Define o ID do site
settings.SITE_ID = 1

# Django user accounts configurações
settings.ACCOUNT_EMAIL_CONFIRMATION_URL = 'core>email-confirm'
settings.ACCOUNT_PASSWORD_EXPIRY = config('ACCOUNT_PASSWORD_EXPIRY', cast=int) # As senhas expiram em x dias e precisam ser trocas após esse tempo
settings.ACCOUNT_PASSWORD_USE_HISTORY = True

# Django Anymail configurações
settings.ANYMAIL = {
    'MAILGUN_API_KEY': config('MAILGUN_API_KEY'),
    'MAILGUN_SENDER_DOMAIN': config('MAILGUN_SENDER_DOMAIN'),
}

settings.DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')
settings.EMAIL_BACKEND = 'anymail.backends.mailgun.EmailBackend'

# Django session security configurações
settings.SESSION_EXPIRE_AT_BROWSER_CLOSE = True
settings.SESSION_SECURITY_EXPIRE_AFTER = config('SESSION_SECURITY_EXPIRE_AFTER') # Define o tempo de inatividade máximo do usuário, caso ele ultrapasse esse tempo, ele deverá fazer login novamente
settings.SESSION_SECURITY_WARN_AFTER = config('SESSION_SECURITY_WARN_AFTER')