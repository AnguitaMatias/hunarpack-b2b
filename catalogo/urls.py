from django.urls import path, reverse_lazy
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
    path('cotizacion/repetir/<int:cotizacion_id>', views.repetir_cotizacion, name='repetir_cotizacion'),
    
    # Portal de clientes
    path('login/', auth_views.LoginView.as_view(template_name='catalogo/login.html'), name='login'),
    path('logout/', views.salir, name='logout'),
    path('mi-historial/', views.mi_historial, name='mi_historial'),
    path('registro/', views.registro, name='registro'),
    path('cambiar-clave/', views.CambiarContrasena.as_view(), name='cambiar_clave'),

    # Flujo para recuperación de contraseñas olvidadas (Exclusivo clientes)
    path('reiniciar-password/', auth_views.PasswordResetView.as_view(
        template_name='catalogo/password_reset_form.html',
        email_template_name='catalogo/password_reset_email.html',
        subject_template_name='catalogo/password_reset_subject.txt',
        success_url=reverse_lazy('password_reset_done')
    ), name='password_reset'),
    path('reiniciar-password/enviado/', auth_views.PasswordResetDoneView.as_view(
        template_name='catalogo/password_reset_done.html'
    ), name='password_reset_done'),
    path('reiniciar/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='catalogo/password_reset_confirm.html',
        success_url=reverse_lazy('password_reset_complete')
    ), name='password_reset_confirm'),
    path('reiniciar/completado/', auth_views.PasswordResetCompleteView.as_view(
        template_name='catalogo/password_reset_complete.html'
    ), name='password_reset_complete'),

    # Panel Admin
    path('panel/', views.dashboard, name='dashboard'),
    path('panel/cotizacion/<int:cotizacion_id>/precios/', views.fijar_precios_cotizacion, name='fijar_precios'),
    path('panel/personal/', views.gestion_personal, name='gestion_personal'),
    path('panel/personal/editar/<int:user_id>/', views.editar_staff, name='editar_staff'),
    path('panel/personal/eliminar/<int:user_id>/', views.eliminar_staff, name='eliminar_staff'),
    path('panel/simular/', views.simular_cotizacion, name='simular_cotizacion'),
]