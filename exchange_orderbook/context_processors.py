from django.conf import settings
from django_otp import user_has_device


def exchange(request):
	return {
		'STOCK_CHART_THEME': settings.STOCK_CHART_THEME
	}