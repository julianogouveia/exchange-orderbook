from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class Config(AppConfig):
	name = 'exchange_core'
	verbose_name = _('Exchange')