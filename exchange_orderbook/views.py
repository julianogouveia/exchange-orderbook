from datetime import timedelta
from decimal import Decimal

from django.views.generic import TemplateView, View
from django.utils.decorators import method_decorator
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, F
from jsonview.decorators import json_view
from account.decorators import login_required

from exchange_core.models import Currencies, Accounts
from exchange_orderbook.models import BaseCurrencies, CurrencyPairs, Orders
from exchange_orderbook.forms import OrderForm
from exchange_orderbook.choices import CREATED_STATE, EXECUTED_STATE, BID_SIDE, ASK_SIDE


@method_decorator([login_required], name='dispatch')
class OrdersView(TemplateView):
    template_name = 'orderbook/orders.html'

    def get_context_data(self):
        context = super().get_context_data()
        context['base_currencies'] = []

        for base_currency in BaseCurrencies.objects.order_by('order'):
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
                user.profile[market_session_name] = CurrencyPairs.objects.filter(
                    base_currency__currency__symbol=symbol).first().pk

            user.save()

            market = CurrencyPairs.objects.get(pk=user.profile[market_session_name])

            return {'base_currency': symbol, 'market_currency': market.currency.symbol, 'market_pk': market.pk}

        return {'status': 'error'}


@method_decorator([login_required, json_view], name='dispatch')
class UpdateMarketCurrencyView(View):
    def post(self, request):
        user = request.user
        market_symbol = request.POST['symbol']
        base_currency = user.profile[settings.ORDERBOOK_BASE_CURRENCY_SESSION_NAME]
        market_session_name = settings.ORDERBOOK_MARKET_SESSION_NAME + '_' + base_currency
        market = CurrencyPairs.objects.get(base_currency__currency__symbol=base_currency, currency__symbol=market_symbol)
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
            market_currency = CurrencyPairs.objects.filter(base_currency__currency__symbol=base_currency).first().pk
            user.profile[market_session_name] = market_currency
            user.save()

        market = CurrencyPairs.objects.get(pk=user.profile[market_session_name])

        return {'base_currency': base_currency, 'market_currency': market.currency.symbol, 'market_pk': market.pk}


@method_decorator([login_required, json_view], name='dispatch')
class MarketsView(View):
    def get(self, request):
        base_currency = BaseCurrencies.objects.get(currency__symbol=request.GET['base_currency'])
        markets = []

        for market in CurrencyPairs.objects.filter(base_currency=base_currency):
            price_qs = Orders.objects.select_related('market__base_currency__currency', 'market__currency').filter(market=market, status=Orders.STATUS.executed, type=Orders.SIDES.s).order_by('-modified')
            price = Decimal('0.00')

            if price_qs:
                price = price_qs.first().price

            _24_hours_ago = timezone.now() - timedelta(hours=24)
            v_aggregate = Orders.objects.select_related('market__base_currency__currency', 'market__currency')\
                .filter(type=Orders.SIDES.s, status=Orders.STATUS.executed, market=market, created__gte=_24_hours_ago)\
                .aggregate(volume=Sum(F('price') * F('amount')))
            volume = round(v_aggregate['volume'] or Decimal('0.00'), 8)

            markets.append({
                'pk': market.pk,
                'base_currency': market.base_currency.currency.symbol,
                'name': market.quote_currency.name,
                'currency': market.quote_currency.symbol,
                'min_price': market.min_price,
                'max_price': market.max_price,
                'price': '{:8f}'.format(price),
                'volume': '{:8f}'.format(volume)
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
                Orders.SIDES.s: order.market.currency.pk,
                Orders.SIDES.b: order.market.base_currency.currency.pk
            }

            # Armazena os valores que deverao ser comparados com o saldo da conta
            compare_amounts = {
                Orders.SIDES.s: order.amount,
                Orders.SIDES.b: order.price * order.amount
            }

            # Pega a conta que devera ser usada para comprar o saldo
            compare_account = Accounts.objects.get(user=order.user, currency=compare_currencies[order.type])

            # Valida os dados
            if order.price <= Decimal('0.00'):
                return {'error': _("Price is 0")}
            if order.amount <= Decimal('0.00'):
                return {'error': _("Amount is 0")}
            # Compara o valor da order com o saldo de deposito da conta
            if compare_amounts[order.type] > compare_account.deposit:
                return {'error': _("You does not have enought balance")}

            # Reserva o saldo da order
            compare_account.deposit -= compare_amounts[order.type]
            compare_account.reserved += compare_amounts[order.type]
            compare_account.save()

            # Com tudo certo, salva a order no banco
            order.fee_currency = compare_account.currency
            order.save()

            return {'order': order.pk}


@method_decorator([login_required, json_view], name='dispatch')
class BaseOrdersView(View):
    order_type = None
    order_state = CREATED_STATE
    order_by = []

    def get(self, request):
        only_my_orders = request.GET.get('only_my_orders', '')

        if settings.ORDERBOOK_BASE_CURRENCY_SESSION_NAME in request.user.profile:
            base_currency = request.user.profile[settings.ORDERBOOK_BASE_CURRENCY_SESSION_NAME]
        else:
            base_currency = BaseCurrencies.objects.first().currency.symbol

        market_session_name = settings.ORDERBOOK_MARKET_SESSION_NAME + '_' + base_currency
        market_pk = request.user.profile[market_session_name]
        market = CurrencyPairs.objects.get(pk=market_pk)

        filter_kwargs = {
            'market': market,
            'type__in': self.order_type,
            'status': self.order_state
        }

        if len(only_my_orders) > 0:
            filter_kwargs.update({'user': request.user})

        orders_queryset = Orders.objects.select_related('market__base_currency__currency', 'market__currency').filter(**filter_kwargs).order_by(*self.order_by)[:settings.ORDERBOOK_TABLE_LIMIT]
        orders = []

        for order in orders_queryset:
            orders.append({
                'pk': order.pk,
                'side': order.type_name,
                'updated': order.modified,
                'price_currency': market.base_currency.currency.symbol,
                'price': '{:8f}'.format(order.price),
                'amount_currency': market.currency.symbol,
                'amount': '{:8f}'.format(order.amount),
                'total': '{:8f}'.format(round(order.total, 8)),
                'is_mine': request.user.pk == order.user.pk
            })

        return orders


@method_decorator([login_required, json_view], name='dispatch')
class GetAvailableBalanceView(View):
    def post(self, request):
        currency = Currencies.objects.get(symbol=request.POST['symbol'])
        account = Accounts.objects.get(user=request.user, currency=currency)
        return {'available_balance': '{:8f}'.format(account.deposit)}


# Cancela a order do usuario
@method_decorator([login_required, json_view], name='dispatch')
class CancelMyOrderView(View):
    def post(self, request):
        with transaction.atomic():
            order = Orders.objects.get(pk=request.POST['pk'], user=request.user, status=Orders.STATUS.created)
            order.status = Orders.STATUS.canceled
            order.save()

            if order.type == Orders.SIDES.s:
                account = Accounts.objects.get(user=request.user, currency=order.market.currency)
                account.reserved -= order.amount
                account.deposit += order.amount
                account.save()
            elif order.type == Orders.SIDES.b:
                account = Accounts.objects.get(user=request.user, currency=order.market.base_currency.currency)
                account.reserved -= order.total
                account.deposit += order.total
                account.save()

        return {'message': _("Your order has been canceled")}



class BuyOrdersView(BaseOrdersView):
    order_type = [BID_SIDE]
    order_by = ['-price', 'created']


class SellOrdersView(BaseOrdersView):
    order_type = [ASK_SIDE]
    order_by = ['price', 'created']


class ExecutedOrdersView(BaseOrdersView):
    order_type = [ASK_SIDE, BID_SIDE]
    order_state = EXECUTED_STATE
    order_by = ['-modified', 'price']
