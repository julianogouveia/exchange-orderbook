from django.conf import settings


def exchange(request):
    return {
        'TRADINGVIEW_THEME': settings.TRADINGVIEW_THEME,
        'TRADINGVIEW_HEIGHT': settings.TRADINGVIEW_HEIGHT
    }
