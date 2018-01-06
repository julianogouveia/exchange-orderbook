from setuptools import setup, find_packages


__VERSION__ = '0.1'


setup(
	name='exchange-orderbook',
	version=__VERSION__,
	description='Exchange orderbook package',
	author='Juliano Gouveia',
	author_email='juliano@neosacode.com',
	keywords='exchange, orderbook, neosacode, coins',
	packages=find_packages(exclude=[]),
	python_requires='>=3.5'
)