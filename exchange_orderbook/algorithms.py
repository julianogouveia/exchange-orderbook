import gevent
from decimal import Decimal
from django.db import transaction
from django.conf import settings
from exchange_core.models import Accounts
from exchange_core.utils import close_db_connection
from exchange_orderbook.models import Orders, Matchs, Markets

"""
 https://stackoverflow.com/questions/13112062/which-are-the-order-matching-algorithms-most-commonly-used-by-electronic-financi
 http://people.hss.caltech.edu/~pbs/fm/chunks/ch10.html
 https://www.cmegroup.com/confluence/display/EPICSANDBOX/Matching+Algorithms
 https://www.zerohedge.com/news/2014-04-19/timestamp-fraud-rigged-market-explained-one-simple-animation
"""


# This proccess a order using the FIFO continuous trading algorithm
class FIFO:
    def get_accounts(self, order):
        active_account = Accounts.objects.get(user_id=order.user_id,
                                              currency__id=order.market.base_currency.currency_id)
        passive_account = Accounts.objects.get(user_id=order.user_id, currency__id=order.market.currency_id)
        return [active_account, passive_account]

    def get_fee(self, amount, type):
        if type == 'active':
            return amount * settings.INTERMEDIATION_ACTIVE_FEE
        elif type == 'passive':
            return amount * settings.INTERMEDIATION_PASSIVE_FEE

    def negotiate(self, bid, ask, bid_amount, ask_amount, a_active_account, b_active_account, a_passive_account, b_passive_account, give_back=None):
        # Faz a distincao entre order ativa e passsiva, a order ativa e sempre a order mais recente, pois ela deu origem a operacao
        if bid.created > ask.created:
            active_order = bid
            passive_order = ask
            active_amount = bid_amount
            passive_amount = ask_amount
            bid_amount_with_fee = bid_amount - self.get_fee(bid_amount, 'active')
            ask_amount_with_fee = ask_amount - self.get_fee(ask_amount, 'passive')
        else:
            active_order = ask
            passive_order = bid
            active_amount = ask_amount
            passive_amount = bid_amount
            bid_amount_with_fee = bid_amount - self.get_fee(bid_amount, 'passive')
            ask_amount_with_fee = ask_amount - self.get_fee(ask_amount, 'active')

        b_active_account.reserved -= bid_amount
        b_active_account.save()
        a_active_account.deposit += bid_amount_with_fee
        a_active_account.save()
        a_passive_account.reserved -= ask_amount
        a_passive_account.save()
        b_passive_account.deposit += ask_amount_with_fee
        b_passive_account.save()

        match = Matchs()
        match.active_fee = self.get_fee(active_amount, 'active')
        match.passive_fee = self.get_fee(passive_amount, 'passive')
        match.active_order = active_order
        match.passive_order = passive_order
        match.save()

        # Give back the amount to user
        if give_back:
            b_active_account.reserved -= give_back
            b_active_account.deposit += give_back
            b_active_account.save()

        return (bid_amount_with_fee, ask_amount_with_fee)

    def finish_order(self, order, fee=None):
        order.status = Orders.STATUS.executed
        order.fee = fee
        order.save()
        return order

    def save_bid_price(self, bid, ask):
        bid.price = ask.price
        bid.save()

    def do_exchange(self, bid, ask):
        # Get the buyer active and passive accounts for exchange the amounts
        b_active_account, b_passive_account = self.get_accounts(bid)
        a_active_account, a_passive_account = self.get_accounts(ask)

        if ask.amount < bid.amount:
            bid_total = ask.amount * ask.price
            give_back = abs((bid.price * ask.amount) - (ask.price * ask.amount)) if ask.price < bid.price else None

            bid_fee, ask_fee = self.negotiate(bid, ask, bid_total, ask.amount, a_active_account, b_active_account, a_passive_account, b_passive_account, give_back=give_back)
            self.finish_order(ask, ask_fee)

            # Take out the amount and save the order
            # for not execute the order with the same amount again
            original_bid_amount = bid.amount
            original_bid_price = bid.price
            bid.amount = ask.amount
            bid.save()

            self.finish_order(bid, bid_fee)
            self.save_bid_price(bid, ask)

            # Reset object to create a new one
            bid.pk = None
            bid.price = original_bid_price
            bid.amount = original_bid_amount - ask.amount
            bid.status = Orders.STATUS.created
            bid.save()

        elif ask.amount > bid.amount:
            bid_total = bid.amount * ask.price
            give_back = abs((bid.price * bid.amount) - (ask.price * bid.amount)) if ask.price < bid.price else None

            bid_fee, ask_fee = self.negotiate(bid, ask, bid_total, bid.amount, a_active_account, b_active_account, a_passive_account, b_passive_account, give_back=give_back)
            self.finish_order(bid, bid_fee)

            # Take out the amount and save the order
            # for not execute the order with the same amount again
            original_ask_amount = ask.amount
            ask.amount = bid.amount
            ask.save()

            self.finish_order(ask, ask_fee)

            # Reset object to create a new one
            ask.pk = None
            ask.amount = original_ask_amount - bid.amount
            ask.status = Orders.STATUS.created
            ask.save()

        elif ask.amount == bid.amount:
            bid_total = bid.amount * ask.price
            give_back = abs((bid.price * bid.amount) - (ask.price * bid.amount)) if ask.price < bid.price else None

            bid_fee, ask_fee = self.negotiate(bid, ask, bid_total, ask.amount, a_active_account, b_active_account, a_passive_account, b_passive_account, give_back=give_back)
            self.finish_order(ask, ask_fee)

            self.finish_order(bid, bid_fee)
            self.save_bid_price(bid, ask)

    @close_db_connection
    def execute(self, market):
        with transaction.atomic():
            ask_orders = Orders.objects.filter(type=Orders.TYPES.s, status=Orders.STATUS.created, market=market).order_by('price', 'created')
            bid_orders = Orders.objects.filter(type=Orders.TYPES.b, status=Orders.STATUS.created, market=market).order_by('-price', 'created')

            # Stops function execution if one of match queues are empty
            if not ask_orders or not bid_orders:
                return

            high_ask = ask_orders.first()
            has_match = False

            # Loop over bid orders for validate them
            for bid_order in bid_orders:
                high_bid = bid_order

                # Skip to next bid if match orders can't owned to the same user
                if high_ask.user_id == high_bid.user_id:
                    continue

                # Stops function execution if there is no market price match
                if high_ask.price > high_bid.price:
                    break

                # Stops the loop, and assume that a perfect match was found
                has_match = True
                break

            # Stops if does not exist any possible match
            if has_match:
                # Exchange matched orders
                self.do_exchange(high_bid, high_ask)

    def spawn(self):
        gevent.wait([gevent.spawn(self.execute, market)
                    for market in Markets.objects.all()])
