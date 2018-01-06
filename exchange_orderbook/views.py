import importlib

from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from account.decorators import login_required


@method_decorator([login_required], name='dispatch')
class OrdersView(TemplateView):
	template_name = 'orderbook/orders.html'
