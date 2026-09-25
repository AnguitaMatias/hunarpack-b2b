from django.contrib import admin
from django.utils.html import format_html
from .models import Categoria, Producto, Cotizacion, DetalleCotizacion

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

# Inline para ver los productos desde el /admin
class DetalleCotizacionInline(admin.TabularInline):
    model = DetalleCotizacion
    extra = 0
    readonly_fields = ('producto', 'precio_unitario', 'cantidad', 'subtotal')
    can_delete = False

@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'empresa', 'nombre_contacto', 'telefono', 'total', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'fecha_creacion')
    search_fields = ('empresa', 'nombre_contacto', 'email', 'rut_empresa')
    list_editable = ('estado',)
    inlines = [DetalleCotizacionInline]
    readonly_fields = ('fecha_creacion', 'total')