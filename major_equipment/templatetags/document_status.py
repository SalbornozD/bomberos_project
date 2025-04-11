from django import template
from django.utils.html import format_html
from django.utils.dateformat import format as date_format

register = template.Library()

@register.simple_tag
def document_status_badge(status, label="Documento", date=None):
    if not status:
        status = 'sin información'

    status = status.lower()

    badge_classes = {
        'vigente': 'success',
        'por vencer': 'warning',
        'vencido': 'danger',
        'vencida': 'danger',
        'sin información': 'light',
    }

    css_class = badge_classes.get(status, 'light')

    # Formatear fecha legible si existe
    formatted_date = date_format(date, 'd \d\e F \d\e Y') if date else "Sin fecha"
    tooltip = f"{status.capitalize()} - {formatted_date}"

    return format_html(
        f'<span class="badge text-bg-{css_class}" title="{tooltip}">{label}</span>'
    )
