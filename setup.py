from setuptools import setup, find_packages


__VERSION__ = '0.1'

REQUIREMENTS = [
	'django>=2.0', 
	'django-model-utils', 
	'Pillow', 
	'django-two-factor-auth', 
	'dj_database_url', 
	'prettyconf', 
	'psycopg2',
	'django-extensions',
	'django-user-accounts',
	'django-anymail',
	'django-widget-tweaks==0.0.0.1.1',
	'django-session-security==0.0.0.1.1',
]

DEPENDENCIES = [
	'https://github.com/jazzband/django-widget-tweaks/tarball/35822bf5bd29fa8ec9976993b9a3bf9b5241c8d6#egg=django-widget-tweaks-0.0.0.1.1',
	'https://github.com/yourlabs/django-session-security/tarball/aff5adb5f884ecd20f7c160ef26bd25c5114fd78#egg=django-session-security-0.0.0.1.1',
]

setup(
	name='exchange-core',
	version=__VERSION__,
	description='Exchange core package',
	author='Juliano Gouveia',
	author_email='juliano@neosacode.com',
	keywords='exchange, neosacode, coins',
	install_requires=REQUIREMENTS,
	dependency_links=DEPENDENCIES,
	packages=find_packages(exclude=[]),
	python_requires='>=3.5'
)