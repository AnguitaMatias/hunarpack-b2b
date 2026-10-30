from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# MODELOS DEL CATÁLOGO

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre de la Categoría")
    imagen = models.ImageField(upload_to='categorias/', blank=True, null=True, verbose_name="Imagen de Categoría")
    
    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

class Producto(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='productos')
    nombre = models.CharField(max_length=200, verbose_name="Nombre del Producto Base")
    descripcion = models.TextField(blank=True, verbose_name="Descripción General")
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True, verbose_name="Imagen Principal del Producto")
    
    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Producto Base"
        verbose_name_plural = "Productos Base"

class VarianteProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='variantes')
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código / SKU")
    nombre_variante = models.CharField(max_length=200, verbose_name="Nombre de la Variante (ej. Caja 50x50)")
    
    # Atributos
    unidades_por_caja = models.PositiveIntegerField(default=1, verbose_name="Unidades por Caja")
    nota = models.TextField(blank=True, null=True, verbose_name="Nota Adicional")
    apto_microondas = models.BooleanField(default=False, verbose_name="¿Apto para Microondas?")
    dimensiones = models.CharField(max_length=100, blank=True, null=True, verbose_name="Dimensiones")
    material = models.CharField(max_length=100, blank=True, null=True, verbose_name="Material")
    presentacion = models.CharField(max_length=100, blank=True, null=True, verbose_name="Presentación")
    es_ecologico = models.BooleanField(default=False, verbose_name="¿Es Ecológico?")
    
    # Precio y stock
    precio = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Precio (CLP)")
    stock_actual = models.IntegerField(default=0, verbose_name="Stock Actual")
    stock_minimo = models.IntegerField(default=5, verbose_name="Stock Crítico")
    
    # Imagen principal de la variante
    imagen_principal = models.ImageField(upload_to='variantes/', blank=True, null=True, verbose_name="Imagen Principal Variante")

    def estado_stock(self):
        if self.stock_actual <= 0: return 'Agotado'
        elif self.stock_actual <= self.stock_minimo: return 'Crítico'
        return 'Disponible'

    def __str__(self):
        return f"{self.producto.nombre} - {self.nombre_variante}"

    class Meta:
        verbose_name = "Variante de Producto"
        verbose_name_plural = "Variantes de Productos"

class ImagenVariante(models.Model):
    variante = models.ForeignKey(VarianteProducto, on_delete=models.CASCADE, related_name='imagenes_extra')
    imagen = models.ImageField(upload_to='variantes/galeria/', verbose_name="Imagen Adicional")
    
    def __str__(self):
        return f"Imagen extra de {self.variante.codigo}"

# MODELOS DE COTIZACIÓN Y RESERVAS

class Cotizacion(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_REVISION', 'En revisión'),
        ('RESPONDIDA', 'Respondida'),
        ('FINALIZADA', 'Finalizada'),
    ]
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cotizaciones')
    ejecutivo = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cotizaciones_gestionadas')
    
    empresa = models.CharField(max_length=150, verbose_name="Razón Social / Empresa")
    rut_empresa = models.CharField(max_length=15, blank=True, null=True, verbose_name="RUT Empresa")
    nombre_contacto = models.CharField(max_length=120, verbose_name="Nombre de Contacto")
    telefono = models.CharField(max_length=20, verbose_name="Teléfono")
    email = models.EmailField(verbose_name="Correo Electrónico")
    pais = models.CharField(max_length=100, default='Chile')
    mensaje = models.TextField(blank=True, null=True, verbose_name="Notas adicionales")
    
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Solicitud")
    dias_validez = models.IntegerField(default=15)
    
    total = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Total Cotizado")
    descuento_total = models.IntegerField(default=0)
    iva = models.IntegerField(default=0)
    subtotal_neto = models.IntegerField(default=0)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')

    class Meta:
        verbose_name = "Cotización"
        verbose_name_plural = "Cotizaciones"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Cotización #{self.id} - {self.empresa}"

class DetalleCotizacion(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='detalles')
    variante = models.ForeignKey(VarianteProducto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Precio Unitario")
    porcentaje_descuento = models.IntegerField(default=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=0)

    def __str__(self):
        return f"{self.cantidad} x {self.variante.nombre_variante}"

class ReservarStock(models.Model):
    session_key = models.CharField(max_length=40)
    variante = models.ForeignKey(VarianteProducto, on_delete=models.CASCADE, related_name='reservas')
    cantidad = models.PositiveIntegerField(default=0)
    fecha_creacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Reserva: {self.cantidad} de {self.variante.codigo}"