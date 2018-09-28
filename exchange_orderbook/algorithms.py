import gevent
from django.db import transaction
from django.conf import settings
from django.utils import timezone
from exchange_core.models import Accounts
from exchange_core.utils import close_db_connection
from exchange_orderbook.models import Orders, Trades, CurrencyPairs
from exchange_orderbook.choices import CREATED_STATE, EXECUTED_STATE, ASK_SIDE, BID_SIDE

"""
 https://stackoverflow.com/questions/13112062/which-are-the-order-matching-algorithms-most-commonly-used-by-electronic-financi
 http://people.hss.caltech.edu/~pbs/fm/chunks/ch10.html
 https://www.cmegroup.com/confluence/display/EPICSANDBOX/Matching+Algorithms
 https://www.zerohedge.com/news/2014-04-19/timestamp-fraud-rigged-market-explained-one-simple-animation
 https://www.investopedia.com/terms/i/isocurrencycode.asp
 https://www.investopedia.com/terms/b/basecurrency.asp
 https://www.investopedia.com/terms/q/quotecurrency.asp
"""


MAKER_TYPE = 'active'
TAKER_TYPE = 'passive'


# This proccess a order using the FIFO continuous trading algorithm
class FIFO:
    def get_accounts(self, order):
        active_account = Accounts.objects.get(user_id=order.user_id, currency__id=order.currency_pair.base_currency.currency_id)
        passive_account = Accounts.objects.get(user_id=order.user_id, currency__id=order.currency_pair.quote_currency_id)
        return [active_account, passive_account]

    def get_fee(self, amount, type):
        if type == MAKER_TYPE:
            return amount * settings.INTERMEDIATION_ACTIVE_FEE
        elif type == TAKER_TYPE:
            return amount * settings.INTERMEDIATION_PASSIVE_FEE

    def trade(self, bid, ask, bid_amount, ask_amount, a_active_account, b_active_account, a_passive_account, b_passive_account, give_back=None):
        # Makes the distinction between maker active order and passive order
        if bid.created > ask.created:
            active_order = bid
            passive_order = ask
            active_amount = bid_amount
            passive_amount = ask_amount
            bid_fee = self.get_fee(bid_amount, TAKER_TYPE)
            ask_fee = self.get_fee(ask_amount, MAKER_TYPE)
            bid_amount_with_fee = bid_amount - bid_fee
            ask_amount_with_fee = ask_amount - ask_fee
        else:
            active_order = ask
            passive_order = bid
            active_amount = ask_amount
            passive_amount = bid_amount
            bid_fee = self.get_fee(bid_amount, MAKER_TYPE)
            ask_fee = self.get_fee(ask_amount, TAKER_TYPE)
            bid_amount_with_fee = bid_amount - bid_fee
            ask_amount_with_fee = ask_amount - ask_fee

        b_active_account.reserved -= bid_amount
        b_active_account.save()
        a_active_account.deposit += bid_amount_with_fee
        a_active_account.save()

        a_passive_account.reserved -= ask_amount
        a_passive_account.save()
        b_passive_account.deposit += ask_amount_with_fee
        b_passive_account.save()

        trade = Trades()
        trade.taker_fee = self.get_fee(active_amount, TAKER_TYPE)
        trade.maker_fee = self.get_fee(passive_amount, MAKER_TYPE)
        trade.taker_order = active_order
        trade.maker_order = passive_order
        trade.save()

        # Give back the amount to user
        if give_back:
            b_active_account.reserved -= give_back
            b_active_account.deposit += give_back
            b_active_account.save()

        return (bid_fee, ask_fee)

    def finish_order(self, order, fee=None):
        order.state = EXECUTED_STATE
        order.fee = fee
        order.executed = timezone.now()
        order.save()
        return order

    def save_bid_price(self, bid, ask):
        bid.price = ask.price
        bid.save()

    def do_exchange(self, bid, ask):
        # Get the buyer active and passive accounts for exchange the amounts
        b_active_account, b_passive_account = self.get_accounts(bid)
        a_active_account, a_passive_account = self.get_accounts(ask)

        if ask.qty < bid.qty:
            bid_total = ask.qty * ask.price
            give_back = abs((bid.price * ask.qty) - (ask.price * ask.qty)) if ask.price < bid.price else None

            bid_fee, ask_fee = self.trade(bid, ask, bid_total, ask.qty, a_active_account, b_active_account,
                                          a_passive_account, b_passive_account, give_back=give_back)
            self.finish_order(ask, ask_fee)

            # Take out the amount and save the order
            # for not execute the order with the same amount again
            original_bid_amount = bid.qty
            original_bid_price = bid.price
            bid.qty = ask.qty
            bid.save()

            self.finish_order(bid, bid_fee)
            self.save_bid_price(bid, ask)

            # Reset object to create a new one
            bid.pk = None
            bid.price = original_bid_price
            bid.qty = original_bid_amount - ask.qty
            bid.state = CREATED_STATE
            bid.save()

        elif ask.qty > bid.qty:
            bid_total = bid.qty * ask.price
            give_back = abs((bid.price * bid.qty) - (ask.price * bid.qty)) if ask.price < bid.price else None

            bid_fee, ask_fee = self.trade(bid, ask, bid_total, bid.qty, a_active_account, b_active_account,
                                          a_passive_account, b_passive_account, give_back=give_back)
            self.finish_order(bid, bid_fee)

            # Take out the amount and save the order
            # for not execute the order with the same amount again
            original_ask_amount = ask.qty
            ask.qty = bid.qty
            ask.save()

            self.finish_order(ask, ask_fee)

            # Reset object to create a new one
            ask.pk = None
            ask.qty = original_ask_amount - bid.qty
            ask.state = CREATED_STATE
            ask.save()

        elif ask.qty == bid.qty:
            bid_total = bid.qty * ask.price
            give_back = abs((bid.price * bid.qty) - (ask.price * bid.qty)) if ask.price < bid.price else None
            bid_fee, ask_fee = self.trade(bid, ask, bid_total, ask.qty, a_active_account, b_active_account, a_passive_account, b_passive_account, give_back=give_back)

            self.finish_order(ask, ask_fee)
            self.finish_order(bid, bid_fee)
            self.save_bid_price(bid, ask)

    @close_db_connection
    def execute(self, currency_pair):
        with transaction.atomic():
            ask_orders = Orders.objects.filter(side=ASK_SIDE, state=CREATED_STATE, currency_pair=currency_pair).order_by('price', 'created')
            bid_orders = Orders.objects.filter(side=BID_SIDE, state=CREATED_STATE, currency_pair=currency_pair).order_by('-price', 'created')

            # Stops function execution if one of match queues are empty
            if not ask_orders or not bid_orders:
                return

            high_ask = ask_orders.first()
            has_match = False

            # Loop over bid orders for validate them
            for bid_order in bid_orders:
                high_bid = bid_order

                # Skip to next bid if match orders can't owned to the same user
                if high_ask.user_id == high_bid.user_id and not settings.ALLOW_SAME_USER_ORDER_MATCH:
                    continue

                # Stops function execution if there is no currency_pair price match
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
        gevent.wait([gevent.spawn(self.execute, market) for market in CurrencyPairs.objects.all()])
