from django.utils.translation import ugettext_lazy as _


BID_SIDE = 'bid'
ASK_SIDE = 'ask'

SIDE_CHOICES = (
    (BID_SIDE, _('Bid')),
    (ASK_SIDE, _('Ask'))
)


CREATED_STATE = 'created'
EXECUTED_STATE = 'executed'
CANCELED_STATE = 'canceled'

STATE_CHOICES = (
    (CREATED_STATE, _('Created')),
    (EXECUTED_STATE, _('Executed')),
    (CANCELED_STATE, _('Canceled'))
)