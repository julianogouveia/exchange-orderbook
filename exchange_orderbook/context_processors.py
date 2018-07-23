from django.conf import settings


def exchange(request):
    return {
        'STOCK_CHART_THEME': settings.STOCK_CHART_THEME,
        'STOCK_CHART_HEIGHT': settings.STOCK_CHART_HEIGHT
    }
