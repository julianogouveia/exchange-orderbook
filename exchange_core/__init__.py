from django.conf import settings


# Define o nome do pacote
PACKAGE_NAME = 'exchange_core'

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

# Define a model do usuário como sendo a model Users desse pacote
settings.AUTH_USER_MODEL = PACKAGE_NAME + '.Users'

# Define o template do Two Factor para ser usado no login
settings.LOGIN_URL = 'two_factor:login'

# Define o tempo máximo de inatividade para 15 minutos
settings.SESSION_COOKIE_AGE = 15 * 60