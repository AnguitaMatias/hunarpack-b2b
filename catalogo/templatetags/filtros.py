from django import template

register = template.Library()

@register.filter
def peso(valor):
    """Formatea el número usando separador de miles usando punto (.)"""
    try:
        # formatea a coma y luego lo reemplaza por el punto
        return f"{int(valor):,}".replace(',', '.')
    except (ValueError, TypeError):
        return valor