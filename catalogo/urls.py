from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Rutas generales
    path('', views.lista_productos, name='lista_productos'),
    path('api/carrito/agregar/', views.agregar_al_carrito, name='agregar_al_carrito'),

    # Rutas del carro y checkout
    path('carrito/', views.resumen_carrito, name='resumen_carrito'),
    path('api/carrito/actualizar/', views.actualizar_carrito, name='actualizar_carrito'),
    path('checkout/procesar/', views.procesar_cotizacion, name='procesar_cotizacion'),
    path('cotizacion/<int:cotizacion_id>/pdf/', views.generar_pdf_cotizacion, name='generar_pdf_cotizacion'),
    
    # Portal de clientes
    path('login/', auth_views.LoginView.as_view(template_name='catalogo/login.html'), name='login'),
    path('logout/', views.salir, name='logout'),
    path('mi-historial/', views.mi_historial, name='mi_historial'),
    path('registro/', views.registro, name='registro'),

    # Panel Admin
    path('panel/', views.dashboard, name='dashboard'),
    path('panel/cotizacion/<int:cotizacion_id>/precios/', views.fijar_precios_cotizacion, name='fijar_precios'),
]