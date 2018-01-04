from setuptools import setup, find_packages


__VERSION__ = '0.1'

REQUIREMENTS = [
	'exchange-core==0.0.0.1.1'
	'django>=2.0',
]

DEPENDENCIES = [
	'https://bitbucket.org/neosacode/exchange-core/get/f905030ab327.zip#egg=exchange-core-0.0.0.1.1',
]

setup(
	name='exchange-payments',
	version=__VERSION__,
	description='Exchange payments package',
	author='Juliano Gouveia',
	author_email='juliano@neosacode.com',
	keywords='exchange, payments, neosacode, coins',
	install_requires=REQUIREMENTS,
	dependency_links=DEPENDENCIES,
	packages=find_packages(exclude=[]),
	python_requires='>=3.5'
)