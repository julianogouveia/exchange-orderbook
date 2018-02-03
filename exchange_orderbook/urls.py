from django.urls import re_path, path, include

from . import views


urlpatterns = [
	path('orderbook/', views.OrdersView.as_view(), name='orderbook>orders'),
	path('orderbook/my-base-currency', views.MyBaseCurrencyView.as_view(), name='orderbook>my-base-currency'),
	path('orderbook/update-base-currency', views.UpdateBaseCurrencyView.as_view(), name='orderbook>update-base-currency'),
	path('orderbook/markets', views.MarketsView.as_view(), name='orderbook>markets'),
]