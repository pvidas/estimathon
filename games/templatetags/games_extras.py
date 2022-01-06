from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
@stringfilter
def nicer_exp(value):
    try:
        coeff, exp = value.split('e')
    except ValueError:
        return value

    exp = exp[0].replace('+', '') + exp[1:].lstrip('0')
    if coeff == '1':
        return mark_safe(f'10<sup>{exp}</sup>')
    else:
        return mark_safe(f'{coeff} · 10<sup>{exp}</sup>')