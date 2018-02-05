from django.conf import settings

from exchange_core.models import Accounts
from exchange_orderbook.models import Orders, Earnings


def proccess_order(order):
	user = order.user
	order_active_account = Accounts.objects.get(user=user, currency=order.market.base_currency.currency)
	order_passive_account = Accounts.objects.get(user=user, currency=order.market.currency)

	# Pesquisa uma order que atenda as condicoes de venda e que nao seja do mesmo usuario
	if order.type == Orders.TYPES.b:
		match_orders = Orders.objects.filter(type=Orders.TYPES.s, status=Orders.STATUS.created, price__lte=order.price, amount=order.amount, market=order.market).exclude(user=order.user).order_by('price', 'created')
	elif order.type == Orders.TYPES.s:
		match_orders = Orders.objects.filter(type=Orders.TYPES.b, status=Orders.STATUS.created, price__gte=order.price, amount=order.amount, market=order.market).exclude(user=order.user).order_by('price', 'created')

	# Nao faz nada caso nao exista um match
	if not match_orders.exists():
		return

	match_order = match_orders.first()
	
	match_order_active_account = Accounts.objects.get(user=match_order.user, currency=order.market.base_currency.currency)
	match_order_passive_account = Accounts.objects.get(user=match_order.user, currency=order.market.currency)

	if order.type == Orders.TYPES.b:
		# Se a order for mais barata, extorna a diferenca
		if order.total > match_order.total:
			difference = order.total - match_order.total

			order_active_account.reserved -= difference
			order_active_account.deposit += difference
			order_active_account.save()

		# Faz a troca com as taxas
		active_fee = order.total * settings.INTERMEDIATION_ACTIVE_FEE
		passive_fee = match_order.amount * settings.INTERMEDIATION_PASSIVE_FEE

		# Executa a order ativa
		order_active_account.reserved -= match_order.total
		order_active_account.save()

		match_order_active_account.deposit += match_order.total - active_fee
		match_order_active_account.save()

		# Executa a order passiva
		order_passive_account.reserved += order.amount - passive_fee
		order_passive_account.save()

		match_order_passive_account.deposit -= order.amount
		match_order_passive_account.save()


		# Registra os ganhos do sistema
		earning = Earnings()
		earning.active_order = order
		earning.passive_order = match_order
		earning.active_fee = active_fee
		earning.passive_fee = passive_fee
		earning.save()
	elif order.type == Orders.TYPES.s:
		# Se a order for mais barata, extorna a diferenca
		if match_order.total > order.total:
			difference = match_order.total - order.total

			order_active_account.reserved -= difference
			order_active_account.deposit += difference
			order_active_account.save()

		# Faz a troca com as taxas
		active_fee = match_order.total * settings.INTERMEDIATION_ACTIVE_FEE
		passive_fee = order.amount * settings.INTERMEDIATION_PASSIVE_FEE

		# Executa a order ativa
		match_order_active_account.reserved -= order.total
		match_order_active_account.save()

		order_active_account.deposit += order.total - active_fee
		order_active_account.save()

		# Executa a order passiva
		match_order_passive_account.reserved += order.amount - passive_fee
		match_order_passive_account.save()

		order_passive_account.deposit -= order.amount
		order_passive_account.save()

		# Registra os ganhos do sistema
		earning = Earnings()
		earning.active_order = match_order
		earning.passive_order = order
		earning.active_fee = active_fee
		earning.passive_fee = passive_fee
		earning.save()

	# Muda o status das orders para executadas, se nao serao reprocessadas pelo sistema
	order.status = Orders.STATUS.executed
	order.save()

	match_order.status = Orders.STATUS.executed
	match_order.save()