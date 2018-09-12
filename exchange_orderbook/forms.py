from decimal import Decimal
from django import forms
from django.utils.translation import ugettext_lazy as _

from exchange_orderbook.models import Orders, CurrencyPairs


class OrderForm(forms.ModelForm):
	class Meta:
		model = Orders
		fields = ('currency_pair', 'price', 'amount', 'side',)

	def clean_price(self):
		market = self.cleaned_data['currency_pair']
		price = self.cleaned_data['price']

		if not isinstance(market, CurrencyPairs):
			raise forms.ValidationError(_("Invalid market selected"))

		if market.min_price > price:
			raise forms.ValidationError(_("Min price for this market is {}".format(market.min_price)))

		if market.max_price < price:
			raise forms.ValidationError(_("Max price for this market is {}".format(market.max_price)))

		return price

