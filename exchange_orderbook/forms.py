from django import forms

from exchange_orderbook.models import Orders


class OrderForm(forms.ModelForm):
	class Meta:
		model = Orders
		fields = ('market', 'price', 'amount', 'type',)
