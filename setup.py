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
	'django-tweaks==0.1.1',
]

DEPENDENCIES = [
	'https://github.com/jazzband/django-widget-tweaks/tarball/master#egg=django-tweaks-0.1.1',
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