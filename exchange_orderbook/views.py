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
from exchange_orderbook.choices import CREATED_STATE, CANCELED_STATE, EXECUTED_STATE, BID_SIDE, ASK_SIDE


@method_decorator([login_required], name='dispatch')
class OrdersView(TemplateView):
    template_name = 'orderbook/orders.html'

    def get_context_data(self):
        context = super().get_context_data()
        context['base_currencies'] = []

        for base_currency in BaseCurrencies.objects.order_by('order'):
            context['base_currencies'].append({
                'pk': base_currency.pk,
                'code': base_currency.currency.code
            })

        return context


@method_decorator([login_required, json_view], name='dispatch')
class UpdateBaseCurrencyView(View):
    def post(self, request):
        user = request.user

        if BaseCurrencies.objects.filter(currency__code=request.POST['code']).exists():
            code = request.POST['code']
            user.profile[settings.ORDERBOOK_BASE_CURRENCY_SESSION_NAME] = code
            market_session_name = settings.ORDERBOOK_MARKET_SESSION_NAME + '_' + code

            if not market_session_name in user.profile:
                user.profile[market_session_name] = CurrencyPairs.objects.filter(
                    base_currency__currency__code=code).first().pk

            user.save()

            currency_pair = CurrencyPairs.objects.get(pk=user.profile[market_session_name])

            return {'base_currency': code, 'market_currency': currency_pair.quote_currency.code, 'market_pk': currency_pair.pk}

        return {'status': 'error'}


@method_decorator([login_required, json_view], name='dispatch')
class UpdateMarketCurrencyView(View):
    def post(self, request):
        user = request.user
        currency_code = request.POST['code']
        base_currency = user.profile[settings.ORDERBOOK_BASE_CURRENCY_SESSION_NAME]
        currency_pair_session = settings.ORDERBOOK_MARKET_SESSION_NAME + '_' + base_currency
        currency_pair = CurrencyPairs.objects.get(base_currency__currency__code=base_currency, quote_currency__code=currency_code)
        user.profile[currency_pair_session] = currency_pair.pk
        user.save()

        return {'market_currency': currency_pair.quote_currency.code, 'market_pk': currency_pair.pk}


@method_decorator([login_required, json_view], name='dispatch')
class MyBaseCurrencyView(View):
    def get(self, request):
        user = request.user

        if settings.ORDERBOOK_BASE_CURRENCY_SESSION_NAME in user.profile:
            base_currency = user.profile[settings.ORDERBOOK_BASE_CURRENCY_SESSION_NAME]
        else:
            base_currency = BaseCurrencies.objects.first().currency.code
            user.profile[settings.ORDERBOOK_BASE_CURRENCY_SESSION_NAME] = base_currency
            user.save()

        market_session_name = settings.ORDERBOOK_MARKET_SESSION_NAME + '_' + base_currency

        if market_session_name in user.profile:
            market_currency = request.user.profile[market_session_name]
        else:
            market_currency = CurrencyPairs.objects.filter(base_currency__currency__code=base_currency).first().pk
            user.profile[market_session_name] = market_currency
            user.save()

        currency_pair = CurrencyPairs.objects.get(pk=user.profile[market_session_name])
        return {'base_currency': base_currency, 'market_currency': currency_pair.quote_currency.code, 'market_pk': currency_pair.pk}


@method_decorator([login_required, json_view], name='dispatch')
class MarketsView(View):
    def get(self, request):
        base_currency = BaseCurrencies.objects.get(currency__code=request.GET['base_currency'])
        markets = []

        for currency_pair in CurrencyPairs.objects.filter(base_currency=base_currency):
            sr = ['currency_pair__base_currency__currency', 'currency_pair__quote_currency']
            price_qs = Orders.objects.select_related(*sr).filter(currency_pair=currency_pair, state=EXECUTED_STATE, side=ASK_SIDE).order_by('-modified')
            price = Decimal('0.00')

            if price_qs:
                price = price_qs.first().price

            _24_hours_ago = timezone.now() - timedelta(hours=24)
            v_aggregate = Orders.objects.select_related(*sr)\
                .filter(side=ASK_SIDE, state=EXECUTED_STATE, currency_pair=currency_pair, created__gte=_24_hours_ago)\
                .aggregate(volume=Sum(F('price') * F('qty')))
            volume = round(v_aggregate['volume'] or Decimal('0.00'), 8)

            markets.append({
                'pk': currency_pair.pk,
                'base_currency': currency_pair.base_currency.currency.code,
                'name': currency_pair.quote_currency.name,
                'currency': currency_pair.quote_currency.code,
                'min_price': currency_pair.min_price,
                'max_price': currency_pair.max_price,
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
                ASK_SIDE: order.currency_pair.quote_currency.pk,
                BID_SIDE: order.currency_pair.base_currency.currency.pk
            }

            # Armazena os valores que deverao ser comparados com o saldo da conta
            compare_qtys = {
                ASK_SIDE: order.qty,
                BID_SIDE: order.amount
            }

            # Pega a conta que devera ser usada para comprar o saldo
            compare_account = Accounts.objects.get(user=order.user, currency=compare_currencies[order.side])
            reserved_qty = compare_qtys[order.side]

            # Compara o valor da order com o saldo de deposito da conta
            if reserved_qty > compare_account.deposit:
                return {'error': _("You does not have enought balance")}

            # Reserva o saldo da order
            compare_account.deposit -= reserved_qty
            compare_account.reserved += reserved_qty
            compare_account.save()

            # Com tudo certo, salva a order no banco
            order.fee_currency = compare_account.currency

            # Sets order type to market when needed
            if order_form.cleaned_data['is_market']:
                order.type = Orders.TYPES.market

            order.save()

            return {'order': order.pk}


@method_decorator([login_required, json_view], name='dispatch')
class GetAvailableBalanceView(View):
    def post(self, request):
        currency = Currencies.objects.get(code=request.POST['code'])
        account = Accounts.objects.get(user=request.user, currency=currency)
        return {'available_balance': '{:8f}'.format(account.deposit)}


# Cancela a order do usuario
@method_decorator([login_required, json_view], name='dispatch')
class CancelMyOrderView(View):
    def post(self, request):
        with transaction.atomic():
            order = Orders.objects.get(pk=request.POST['pk'], user=request.user, state=CREATED_STATE)
            order.state = CANCELED_STATE
            order.save()

            if order.side == ASK_SIDE:
                account = Accounts.objects.get(user=request.user, currency=order.currency_pair.quote_currency)
                account.reserved -= order.qty
                account.deposit += order.qty
                account.save()
            elif order.side == BID_SIDE:
                account = Accounts.objects.get(user=request.user, currency=order.currency_pair.base_currency.currency)
                account.reserved -= order.amount
                account.deposit += order.amount
                account.save()

        return {'message': _("Your order has been canceled")}


@method_decorator([login_required, json_view], name='dispatch')
class BaseOrdersView(View):
    order_side = None
    order_state = CREATED_STATE
    order_by = []

    def get(self, request):
        only_my_orders = request.GET.get('only_my_orders', '')

        if settings.ORDERBOOK_BASE_CURRENCY_SESSION_NAME in request.user.profile:
            base_currency = request.user.profile[settings.ORDERBOOK_BASE_CURRENCY_SESSION_NAME]
        else:
            base_currency = BaseCurrencies.objects.first().currency.code

        market_session_name = settings.ORDERBOOK_MARKET_SESSION_NAME + '_' + base_currency
        market_pk = request.user.profile[market_session_name]
        currency_pair = CurrencyPairs.objects.get(pk=market_pk)

        qs_kwargs = {
            'currency_pair': currency_pair,
            'side__in': self.order_side,
            'state': self.order_state
        }

        if self.order_state == EXECUTED_STATE:
            qs_kwargs.update({'taker_orders__isnull': False})

        if only_my_orders:
            qs_kwargs.update({'user': request.user})

        orders_queryset = Orders.objects.select_related('currency_pair__base_currency__currency', 'currency_pair__quote_currency').filter(**qs_kwargs).order_by(*self.order_by)[:settings.ORDERBOOK_TABLE_LIMIT]
        orders = []

        for order in orders_queryset:
            orders.append({
                'pk': order.pk,
                'side': order.side_name,
                'updated': order.modified,
                'price_currency': currency_pair.base_currency.currency.code,
                'price': '{:8f}'.format(order.price),
                'qty_currency': currency_pair.quote_currency.code,
                'qty': '{:8f}'.format(order.qty),
                'amount': '{:8f}'.format(round(order.amount, 8)),
                'is_mine': request.user.pk == order.user.pk
            })

        return orders


class BidOrdersView(BaseOrdersView):
    order_side = [BID_SIDE]
    order_by = ['-price', 'created']


class AskOrdersView(BaseOrdersView):
    order_side = [ASK_SIDE]
    order_by = ['price', 'created']


class ExecutedOrdersView(BaseOrdersView):
    order_side = [ASK_SIDE, BID_SIDE]
    order_state = EXECUTED_STATE
    order_by = ['-modified', 'price']
