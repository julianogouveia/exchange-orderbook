from decimal import Decimal

from django import forms
from django.utils.translation import ugettext_lazy as _

from exchange_orderbook.models import Orders, CurrencyPairs
from exchange_orderbook.choices import CREATED_STATE, ASK_SIDE, BID_SIDE


class OrderForm(forms.ModelForm):
    is_market = forms.BooleanField(initial=False)

    class Meta:
        model = Orders
        fields = ('currency_pair', 'price', 'qty', 'side',)

    def clean_price(self):
        currency_pair = self.cleaned_data['currency_pair']
        price = self.cleaned_data['price']
        is_market = bool(int(self.data['is_market']))
        side = self.data['side']

        if not isinstance(currency_pair, CurrencyPairs):
            raise forms.ValidationError(_("Invalid market selected"))

        opposite_side = ASK_SIDE if side == BID_SIDE else BID_SIDE
        opposite_price_order = 'price' if opposite_side == ASK_SIDE else '-price'
        compare_order = Orders.objects.filter(currency_pair=currency_pair, side=opposite_side, state=CREATED_STATE).order_by(opposite_price_order).first()

        if not compare_order and is_market:
            raise forms.ValidationError(_("Bid/Ask immediately is not allowed by this moment"))

        if is_market and side == ASK_SIDE:
            price = compare_order.price - Decimal('0.00000001')
        elif is_market:
            price = compare_order.price + Decimal('0.00000001')

        if price <= 0:
            raise forms.ValidationError(_("Price for this market must be greater than 0"))
        if currency_pair.min_price > price:
            raise forms.ValidationError(_("Min price for this market is {}".format(currency_pair.min_price)))
        if currency_pair.max_price < price:
            raise forms.ValidationError(_("Max price for this market is {}".format(currency_pair.max_price)))

        return price

    def clean_qty(self):
        currency_pair = self.cleaned_data['currency_pair']
        qty = self.cleaned_data['qty']

        if not isinstance(currency_pair, CurrencyPairs):
            raise forms.ValidationError(_("Invalid market selected"))
        if qty <= 0:
            raise forms.ValidationError(_("Quantity for this market must be greater than 0"))
        if currency_pair.min_qty > qty:
            raise forms.ValidationError(_("Min quantity for this market is {}".format(currency_pair.min_qty)))
        if currency_pair.max_qty < qty:
            raise forms.ValidationError(_("Max quantity for this market is {}".format(currency_pair.max_qty)))

        return qty
