from django.urls import re_path, path, include
from two_factor.urls import urlpatterns as tf_urls

from . import views


urlpatterns = [
	re_path(r'', include(tf_urls)),

	# URLs do pacote
	path('account/forget-password', views.ForgetPasswordView.as_view(), name='core>forget-password'),
	path('account/wallets', views.WalletsView.as_view(), name='core>wallets'),
]