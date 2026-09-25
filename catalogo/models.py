from django.db import models

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre de la Categoría")

    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"


class Producto(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='productos')
    nombre = models.CharField(max_length=200, verbose_name="Nombre del Producto")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    precio = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Precio (CLP)")

    # Sistema de control para el inventario
    stock_actual = models.IntegerField(default=0, verbose_name="Stock Actual")
    stock_minimo = models.IntegerField(default=10, verbose_name="Stock Crítico")

    def estado_stock(self):
        if self.stock_actual <= 0:
            return 'Agotado'
        elif self.stock_actual <= self.stock_minimo:
            return 'Crítico'
        return 'Disponible'
    
    def __str__(self):
        return f"{self.nombre} - Stock: {self.stock_actual}"
    
    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

class Cotizacion(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_REVISION', 'En revisión'),
        ('RESPONDIDA', 'Respondida'),
        ('FINALIZADA', 'Finalizada'),
    ]

    nombre_contacto = models.CharField(max_length=120, verbose_name="Nombre de Contacto")
    empresa = models.CharField(max_length=120, verbose_name="Raz+on Social / Empresa")
    rut_empresa = models.CharField(max_length=15, blank=True, null=True, verbose_name="RUT Empresa")
    email = models.EmailField(verbose_name="Correo Electrónico")
    telefono = models.CharField(max_length=20, verbose_name="Teléfono")
    mensaje = models.TextField(blank=True, null=True, verbose_name="Notas adicionales")
    total = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Total Cotizado")
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Solicitud")

    class Meta:
        verbose_name = "Cotización"
        verbose_name_plural = "Cotizaciones"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Cotización #{self.id} - {self.empresa or self.nombre_contacto}"

class DetalleCotizacion(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=0 , verbose_name="Precio Unitario Histórico")
    cantidad = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=12, decimal_places=0)

    class Meta:
        verbose_name = "Detalle de Cotizacion"
        verbose_name_plural = "Detalles de Cotizacion"

    def __str__(self):
        return f"{self.cantidad} * {self.producto.nombre} (Cotiz #{self.cotizacion.id})"

