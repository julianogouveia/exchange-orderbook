from django.urls import re_path, path, include

from . import views


urlpatterns = [
	path('orderbook/', views.OrdersView.as_view(), name='orderbook>orders'),
]