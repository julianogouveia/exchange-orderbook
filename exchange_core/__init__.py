from django.conf import settings


# Define o nome do pacote
PACKAGE_NAME = 'exchange_core'

# Adiciona os pacotes Two Factor para habilitar a autenticação em dois passos
# Adiciona o pacote Django Extensions para habilitar o shell_plus e o reset_db
settings.INSTALLED_APPS += [
	'django_otp',
    'django_otp.plugins.otp_static',
    'django_otp.plugins.otp_totp',
    'two_factor',
    'django_extensions',
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