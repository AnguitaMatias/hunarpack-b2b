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
    readonly_fields = ('producto', 'cantidad', 'subtotal')
    can_delete = False

@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'empresa', 'nombre_contacto', 'telefono', 'total', 'estado', 'fecha_creacion', 'descargar_pdf')
    list_filter = ('estado', 'fecha_creacion')
    search_fields = ('empresa', 'nombre_contacto', 'email', 'rut_empresa')
    list_editable = ('estado',)
    inlines = [DetalleCotizacionInline]
    readonly_fields = ('fecha_creacion', 'total')

    # Botón del pdf
    def descargar_pdf(self, obj):
        from django.utils.html import format_html
        return format_html(
            '<a class="button" style="background-color: #417690; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none;" href="/cotizacion/{}/pdf/">Descargar PDF</a>',
            obj.id
        )
    descargar_pdf.short_description = 'Documento'

    # Guardar totales de la cotizacion al guardar

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)

        # Calculo del subtotal por fila (cantidad * el precio definido por el staff)
        for i in instances:
            if isinstance(i, DetalleCotizacion):
                i.subtotal = i.cantidad * i.precio_unitario
                i.save()
        formset.save_m2m()

        # Se suman los subtotales u se actualiza el total general
        if form.instance.pk:
            cotizacion = form.instance
            total_general = sum(detalle.subtotal for detalle in cotizacion.detalles.all())
            cotizacion.total = total_general
            cotizacion.save()