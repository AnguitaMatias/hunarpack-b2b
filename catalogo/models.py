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
