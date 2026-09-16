from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_productos, name='lista_productos'),
    path('api/carrito/agregar/', views.agregar_al_carrito, name='agregar_al_carrito'),
    
]