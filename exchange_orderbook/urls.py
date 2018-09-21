from django.urls import path

from . import views


urlpatterns = [
    path('orderbook/', views.OrdersView.as_view(), name='orderbook>orders'),
    path('orderbook/my-base-currency', views.MyBaseCurrencyView.as_view(), name='orderbook>my-base-currency'),
    path('orderbook/update-base-currency', views.UpdateBaseCurrencyView.as_view(), name='orderbook>update-base-currency'),
    path('orderbook/markets', views.MarketsView.as_view(), name='orderbook>markets'),
    path('orderbook/update-market-currency', views.UpdateMarketCurrencyView.as_view(), name='orderbook>update-market-currency'),
    path('orderbook/get-available-balance', views.GetAvailableBalanceView.as_view(), name='orderbook>get-available-balance'),
    path('orderbook/cancel-my-order', views.CancelMyOrderView.as_view(), name='orderbook>cancel-my-order-view'),
    path('orderbook/create-order', views.CreateOrderView.as_view(), name='orderbook>create-order'),
    path('orderbook/buy-orders', views.BidOrdersView.as_view(), name='orderbook>buy-orders'),
    path('orderbook/sell-orders', views.AskOrdersView.as_view(), name='orderbook>sell-orders'),
    path('orderbook/executed-orders', views.ExecutedOrdersView.as_view(), name='orderbook>executed-orders'),
]
