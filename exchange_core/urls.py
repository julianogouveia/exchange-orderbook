from django.urls import re_path, path, include
from two_factor.urls import urlpatterns as tf_urls
from account.views import ConfirmEmailView, PasswordResetView, LogoutView, SettingsView

from . import views


urlpatterns = [
	re_path(r'', include(tf_urls)),
	re_path(r'session_security/', include('session_security.urls')),

	# URLs do pacote
	path('account/reset-password/', views.ResetPasswordView.as_view(), name='core>reset-password'),
	path('account/reset-token/<uidb36>/<token>/', views.ResetTokenView.as_view(), name='core>reset-token'),
	path('account/wallets/', views.WalletsView.as_view(), name='core>wallets'),
	path('account/signup/', views.SignupView.as_view(), name='core>signup'),
	path('account/email-confirm/<key>/', ConfirmEmailView.as_view(), name='core>email-confirm'),
	path('account/settings/', views.AccountSettingsView.as_view(), name='core>settings'),
	path('account/logout/', LogoutView.as_view(), name='core>logout'),
]