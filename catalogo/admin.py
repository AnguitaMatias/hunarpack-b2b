from django.contrib import admin
from django.utils.html import format_html
from .models import Categoria, Producto

# Registro Categoría.
admin.site.register(Categoria)

# Vista producto (personalizada)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio', 'mostrar_alerta_stock')
    # filtro lateral
    list_filter = ('categoria',)
    # barra de búsqueda
    search_fields = ('nombre',)

    def mostrar_alerta_stock(self, obj):
        if obj.stock_actual <= 0:
            return format_html('<b style="color: red;">{}</b>', 'AGOTADO (0)')
        elif obj.stock_actual <= obj.stock_minimo:
            return format_html('<b style="color: orange;">ALERTA: Solo ({})</b>', obj.stock_actual)
        return format_html('<span style="color: green;">OK ({})</span>', obj.stock_actual)
    
    mostrar_alerta_stock.short_description = 'Estado del Inventario'

# Registro Producto con la vista personalizada
admin.site.register(Producto, ProductoAdmin)
