from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

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