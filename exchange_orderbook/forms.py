from django import forms
from django.utils.translation import ugettext_lazy as _

from exchange_orderbook.models import Orders, CurrencyPairs


class OrderForm(forms.ModelForm):
    class Meta:
        model = Orders
        fields = ('currency_pair', 'price', 'qty', 'side',)

    def clean_price(self):
        currency_pair = self.cleaned_data['currency_pair']
        price = self.cleaned_data['price']

        if not isinstance(currency_pair, CurrencyPairs):
            raise forms.ValidationError(_("Invalid market selected"))

        if currency_pair.min_price > price:
            raise forms.ValidationError(_("Min price for this market is {}".format(currency_pair.min_price)))

        if currency_pair.max_price < price:
            raise forms.ValidationError(_("Max price for this market is {}".format(currency_pair.max_price)))

        return price
