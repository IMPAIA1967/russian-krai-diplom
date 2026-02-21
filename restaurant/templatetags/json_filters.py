import json
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name='safe_json')
def safe_json(value):
    """
    Преобразует объект Django в JSON для использования в JavaScript.
    """
    data = {
        'pk': value.pk,
        'first_name': value.first_name,
        'last_name': value.last_name,
        'position': value.position,
        'custom_position': value.custom_position or '',
        'photo': value.photo or '',
        'description': value.description,
        'bio': value.bio or '',
        'instagram': value.instagram or '',
        'telegram': value.telegram or '',
        'order': value.order,
        'is_active': value.is_active,
    }
    return mark_safe(json.dumps(data))