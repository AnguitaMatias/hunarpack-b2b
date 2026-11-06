from .models import VarianteProducto, Categoria, Producto, ImagenVariante
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

# Formulario de registro de clientes
class RegistroClienteForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="Correo Electrónico",
        help_text="Lo usaremos para enviarte cotizaciones y recuperar tu contraseña."
    )
    first_name = forms.CharField(
        required=False,
        label="Nombre",
        max_length=200
    )
    last_name = forms.CharField(
        required=False,
        label="Apellido",
        max_length=200
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Ya existe una cuenta registrada con este correo electrónico."
            )
        return email

# Formulario para crear Categorías.
class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'imagen']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Cajas de Cartón'}),
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
        }

# Formulario para crear productos base.
class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'categoria', 'descripcion', 'imagen']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Cajas de Cartón'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoria'].empty_label = "- Selecciona una categoría -"

#Formulario para crear variantes en los productos.
class VarianteProductoForm(forms.ModelForm):    
    class Meta:
        model = VarianteProducto
        fields = [
            'codigo', 'nombre_variante', 'unidades_por_caja', 'dimensiones', 'material',
            'presentacion', 'precio', 'stock_actual', 'stock_minimo', 'nota', 
            'imagen_principal', 'apto_microondas', 'es_ecologico'
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: CCC-001'}),
            'nombre_variante': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Caja de 25x25'}),
            'unidades_por_caja': forms.NumberInput(attrs={'class': 'form-control'}),
            'dimensiones': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 25 de alto x 25 de ancho x 25 de largo'}),
            'material': forms.TextInput(attrs={'class': 'form-control'}),
            'presentacion': forms.TextInput(attrs={'class': 'form-control'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_actual': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control'}),
            'nota': forms.Textarea(attrs={'class': 'form-control', 'row': 2}),
            'imagen_principal': forms.FileInput(attrs={'class': 'form-control'}),

        }

class ImagenVarianteForm(forms.ModelForm):
    class Meta:
        model = ImagenVariante
        fields = ['imagen']
        widgets = {
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
        }