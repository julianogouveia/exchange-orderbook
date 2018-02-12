from decimal import Decimal
import importlib

from django.views.generic import TemplateView, View
from django.utils.decorators import method_decorator
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.db import transaction
from jsonview.decorators import json_view
from account.decorators import login_required

from exchange_core.models import Accounts
from exchange_orderbook.models import BaseCurrencies, Markets, Orders
from exchange_orderbook.forms import OrderForm
from exchange_orderbook.utils import proccess_order


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
			symbol = request.POST['symbol']
			user.profile[settings.ORDERBOOK_BASE_CURRENCY_SESSION_NAME] = symbol
			market_session_name = settings.ORDERBOOK_MARKET_SESSION_NAME + '_' + symbol

			if not market_session_name in user.profile:
				user.profile[market_session_name] = Markets.objects.filter(base_currency__currency__symbol=symbol).first().pk
			
			user.save()

			market = Markets.objects.get(pk=user.profile[market_session_name])

			return {'base_currency': symbol, 'market_currency': market.currency.symbol, 'market_pk': market.pk}

		return {'status': 'error'}


@method_decorator([login_required, json_view], name='dispatch')
class UpdateMarketCurrencyView(View):
	def post(self, request):
		user = request.user
		market_symbol = request.POST['symbol']
		base_currency = user.profile[settings.ORDERBOOK_BASE_CURRENCY_SESSION_NAME]
		market_session_name = settings.ORDERBOOK_MARKET_SESSION_NAME + '_' + base_currency
		market = Markets.objects.get(base_currency__currency__symbol=base_currency, currency__symbol=market_symbol)
		user.profile[market_session_name] = market.pk
		user.save()

		return {'market_currency': market.currency.symbol, 'market_pk': market.pk}


@method_decorator([login_required, json_view], name='dispatch')
class MyBaseCurrencyView(View):
	def get(self, request):
		user = request.user

		if settings.ORDERBOOK_BASE_CURRENCY_SESSION_NAME in user.profile:
			base_currency = user.profile[settings.ORDERBOOK_BASE_CURRENCY_SESSION_NAME]
		else:
			base_currency = BaseCurrencies.objects.first().currency.symbol
			user.profile[settings.ORDERBOOK_BASE_CURRENCY_SESSION_NAME] = base_currency
			user.save()

		market_session_name = settings.ORDERBOOK_MARKET_SESSION_NAME + '_' + base_currency
		
		if market_session_name in user.profile:
			market_currency = request.user.profile[market_session_name]
		else:
			market_currency = Markets.objects.filter(base_currency__currency__symbol=base_currency).first().pk
			user.profile[market_session_name] = market_currency
			user.save()

		market = Markets.objects.get(pk=user.profile[market_session_name])

		return {'base_currency': base_currency, 'market_currency': market.currency.symbol, 'market_pk': market.pk}


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


@method_decorator([login_required, json_view], name='dispatch')
class CreateOrderView(View):
	def post(self, request):
		with transaction.atomic():
			order_form = OrderForm(request.POST)
			# Retorna os errors do form caso o formulario esteja invalido
			if not order_form.is_valid():
				return {'errors': order_form.errors}

			# Cria a instancia da order, e diz para nao salvar ainda no banco
			order = order_form.save(commit=False)
			# Seta o usuario dono da order
			order.user = request.user
			
			# Armazena um dicionario com a relacao de tipo da order e o campo que deve ser comparado
			# usamos isso para validar o saldo do usuario
			# caso haja saldo na conta, ele pode continuar com a order
			# caso nao haja saldo na conta, um erro sera disparado
			compare_currencies = {
				Orders.TYPES.s: order.market.currency.pk,
				Orders.TYPES.b: order.market.base_currency.currency.pk
			}
			
			# Armazena os valores que deverao ser comparados com o saldo da conta
			compare_amounts = {
				Orders.TYPES.s: order.amount,
				Orders.TYPES.b: order.price * order.amount
			}

			# Pega a conta que devera ser usada para comprar o saldo
			compare_account = Accounts.objects.get(user=order.user, currency=compare_currencies[order.type])

			#Valida os dados
			if order.price <= Decimal('0.00'):
				return {'error': _("Price is 0")}
			if order.amount <= Decimal('0.00'):
				return {'error': _("amount is 0")}
			# Compara o valor da order com o saldo de deposito da conta
			if compare_amounts[order.type] > compare_account.deposit:
				return {'error': _("You does not have enought balance")}
			
			# Reserva o saldo da order
			compare_account.deposit -= compare_amounts[order.type]
			compare_account.reserved += compare_amounts[order.type]
			compare_account.save()

			# Com tudo certo, salva a order no banco
			order.save()

			# Processa a order e negociado em realtime com o mercado
			proccess_order(order)

			return {'order': order.pk}


@method_decorator([login_required, json_view], name='dispatch')
class BaseOrdersView(View):
	order_type = None
	order_status = Orders.STATUS.created

	def get(self, request):
		if settings.ORDERBOOK_BASE_CURRENCY_SESSION_NAME in request.user.profile:
			base_currency = request.user.profile[settings.ORDERBOOK_BASE_CURRENCY_SESSION_NAME]
		else:
			base_currency = BaseCurrencies.objects.first().currency.symbol

		market_session_name = settings.ORDERBOOK_MARKET_SESSION_NAME + '_' + base_currency
		market_pk = request.user.profile[market_session_name]
		market = Markets.objects.get(pk=market_pk)

		orders_queryset = Orders.objects.filter(market=market, type__in=self.order_type, status=self.order_status).order_by('-created')[:100]
		orders = []

		for order in orders_queryset:
			orders.append({
				'type': order.type_name,
				'updated': order.modified,
				'price_currency': market.base_currency.currency.symbol,
				'price': order.price,
				'amount_currency': market.currency.symbol,
				'amount': order.amount,
				'total': round(order.price * order.amount, 8),
				'is_mine': request.user.pk == order.user.pk
			})

		return orders


class BuyOrdersView(BaseOrdersView):
	order_type = [Orders.TYPES.b]


class SellOrdersView(BaseOrdersView):
	order_type = [Orders.TYPES.s]


class ExecutedOrdersView(BaseOrdersView):
	order_type = [Orders.TYPES.s, Orders.TYPES.b]
	order_status = Orders.STATUS.executed