import importlib

from django.views.generic import TemplateView, View
from django.utils.decorators import method_decorator
from django.conf import settings
from jsonview.decorators import json_view
from account.decorators import login_required

from exchange_orderbook.models import BaseCurrencies, Markets


@method_decorator([login_required], name='dispatch')
class OrdersView(TemplateView):
	template_name = 'orderbook/orders.html'

	def get_context_data(self):
		context = super().get_context_data()
		context['base_currencies'] = []

		for base_currency in BaseCurrencies.objects.all():
			context['base_currencies'].append({
				'pk': base_currency.pk,
				'symbol': base_currency.currency.symbol
			})

		return context


@method_decorator([login_required, json_view], name='dispatch')
class UpdateBaseCurrencyView(View):
	def post(self, request):
		user = request.user
		
		if BaseCurrencies.objects.filter(currency__symbol=request.POST['symbol']).exists():
			user.profile[settings.ORDERBOOK_BASE_CURRENCY_SESSION_NAME] = request.POST['symbol']
			user.save()
			return {'status': 'success'}

		return {'status': 'error'}


@method_decorator([login_required, json_view], name='dispatch')
class MyBaseCurrencyView(View):
	def get(self, request):
		if settings.ORDERBOOK_BASE_CURRENCY_SESSION_NAME in request.user.profile:
			base_currency = request.user.profile[settings.ORDERBOOK_BASE_CURRENCY_SESSION_NAME]
		else:
			base_currency = BaseCurrencies.objects.first().currency.symbol

		return {'base_currency': base_currency}


@method_decorator([login_required, json_view], name='dispatch')
class MarketsView(View):
	def get(self, request):
		base_currency = BaseCurrencies.objects.get(currency__symbol=request.GET['base_currency'])
		markets = []

		for market in Markets.objects.filter(base_currency=base_currency):
			markets.append({
				'pk': market.pk,
				'base_currency': market.base_currency.currency.symbol,
				'name': market.currency.name,
				'currency': market.currency.symbol,
				'min_price': market.min_price,
				'max_price': market.max_price
			})

		return markets