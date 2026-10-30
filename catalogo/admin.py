from django.contrib import admin
from django.utils.html import format_html
from .models import Categoria, Producto, VarianteProducto, ImagenVariante, Cotizacion, DetalleCotizacion


# ADMIN DEL CATÁLOGO

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)

class ImagenVarianteInline(admin.TabularInline):
    model = ImagenVariante
    extra = 1

class VarianteProductoInline(admin.StackedInline):
    model = VarianteProducto
    extra = 1
    show_change_link = True

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria')
    list_filter = ('categoria',)
    search_fields = ('nombre',)
    inlines = [VarianteProductoInline]

@admin.register(VarianteProducto)
class VarianteProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre_variante', 'producto', 'precio', 'mostrar_alerta_stock')
    list_filter = ('producto__categoria', 'es_ecologico', 'apto_microondas')
    search_fields = ('codigo', 'nombre_variante', 'producto__nombre')
    inlines = [ImagenVarianteInline]

    def mostrar_alerta_stock(self, obj):
        if obj.stock_actual <= 0:
            return format_html('<b style="color: red;">{}</b>', 'AGOTADO (0)')
        elif obj.stock_actual <= obj.stock_minimo:
            return format_html('<b style="color: orange;">ALERTA: Solo {}</b>', obj.stock_actual)
        return format_html('<span style="color: green;">OK ({})</span>', obj.stock_actual)
    mostrar_alerta_stock.short_description = 'Stock'

# ADMIN DE COTIZACIONES
class DetalleCotizacionInline(admin.TabularInline):
    model = DetalleCotizacion
    extra = 0
    readonly_fields = ('variante', 'cantidad', 'subtotal')
    can_delete = False

@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'empresa', 'nombre_contacto', 'telefono', 'total', 'estado', 'fecha_creacion', 'descargar_pdf')
    list_filter = ('estado', 'fecha_creacion')
    search_fields = ('empresa', 'nombre_contacto', 'email', 'rut_empresa')
    list_editable = ('estado',)
    inlines = [DetalleCotizacionInline]
    readonly_fields = ('fecha_creacion', 'total')

    def descargar_pdf(self, obj):
        return format_html(
            '<a class="button" style="background-color: #417690; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none;" href="/cotizacion/{}/pdf/">📄 PDF</a>', 
            obj.id
        )
    descargar_pdf.short_description = 'Documento'

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, DetalleCotizacion):
                instance.subtotal = instance.cantidad * instance.precio_unitario
                instance.save()
        formset.save_m2m()
        if form.instance.pk:
            cotizacion = form.instance
            total_general = sum(detalle.subtotal for detalle in cotizacion.detalles.all())
            cotizacion.total = total_general
            cotizacion.save()