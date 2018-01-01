from django.urls import re_path, path, include
from two_factor.urls import urlpatterns as tf_urls
from account.views import ConfirmEmailView

from . import views


urlpatterns = [
	re_path(r'', include(tf_urls)),
	re_path(r'session_security/', include('session_security.urls')),

	# URLs do pacote
	path('account/forget-password', views.ForgetPasswordView.as_view(), name='core>forget-password'),
	path('account/wallets', views.WalletsView.as_view(), name='core>wallets'),
	path('account/signup', views.SignupView.as_view(), name='core>signup'),
	path('account/email-confirm/<key>', ConfirmEmailView.as_view(), name='core>email-confirm'),
]