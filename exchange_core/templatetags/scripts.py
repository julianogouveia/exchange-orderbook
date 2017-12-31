import json

from django.template import Library


register = Library()


@register.filter(is_safe=True)
def serialize(data):
    return json.dumps(data)