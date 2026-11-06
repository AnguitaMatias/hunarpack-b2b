from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # --- RUTAS GENERALES ---
    path('', views.landing_page, name='landing_page'),
    path('catalogo/', views.lista_categorias, name='lista_categorias'),
    path('catalogo/categoria/<int:categoria_id>/', views.lista_productos, name='lista_productos'),
    path('producto/<int:producto_id>', views.detalle_producto, name='detalle_producto'),

    # --- RUTAS DEL CARRO Y CHECKOUT ---
    path('api/carrito/agregar/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/', views.resumen_carrito, name='resumen_carrito'),
    path('api/carrito/actualizar/', views.actualizar_carrito, name='actualizar_carrito'),
    path('checkout/procesar/', views.procesar_cotizacion, name='procesar_cotizacion'),
    path('cotizacion/<int:cotizacion_id>/pdf/', views.generar_pdf_cotizacion, name='generar_pdf_cotizacion'),
    path('cotizacion/repetir/<int:cotizacion_id>', views.repetir_cotizacion, name='repetir_cotizacion'),
    
    # --- PORTAL DEL CLIENTE ---
    path('login/', auth_views.LoginView.as_view(template_name='catalogo/auth/login.html'), name='login'),
    path('logout/', views.salir, name='logout'),
    path('mi-historial/', views.mi_historial, name='mi_historial'),
    path('registro/', views.registro, name='registro'),
    path('cambiar-clave/', views.CambiarContrasena.as_view(), name='cambiar_clave'),
    path('mi-perfil/', views.mi_perfil, name='mi_perfil'),

    # --- FLUJO CONTRASEÑA OLVIDADA ---
    path('reiniciar-password/', auth_views.PasswordResetView.as_view(
        template_name='catalogo/auth/password_reset_form.html',
        email_template_name='catalogo/password_reset_email.html',
        subject_template_name='catalogo/password_reset_subject.txt',
        success_url=reverse_lazy('password_reset_done')
    ), name='password_reset'),
    path('reiniciar-password/enviado/', auth_views.PasswordResetDoneView.as_view(
        template_name='catalogo/auth/password_reset_done.html'
    ), name='password_reset_done'),
    path('reiniciar/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='catalogo/auth/password_reset_confirm.html',
        success_url=reverse_lazy('password_reset_complete')
    ), name='password_reset_confirm'),
    path('reiniciar/completado/', auth_views.PasswordResetCompleteView.as_view(
        template_name='catalogo/auth/password_reset_complete.html'
    ), name='password_reset_complete'),

    # --- PANEL DEL ADMIN ---
    path('panel/', views.dashboard, name='dashboard'),
    path('panel/cotizacion/<int:cotizacion_id>/precios/', views.fijar_precios_cotizacion, name='fijar_precios'),
    path('panel/personal/', views.gestion_personal, name='gestion_personal'),
    path('panel/personal/editar/<int:user_id>/', views.editar_staff, name='editar_staff'),
    path('panel/personal/eliminar/<int:user_id>/', views.eliminar_staff, name='eliminar_staff'),
    path('panel/simular/', views.simular_cotizacion, name='simular_cotizacion'),
    path('panel/cotizacion/<int:cotizacion_id>/eliminar/', views.eliminar_cotizacion, name='eliminar_cotizacion'),

    # --- CRUD DEL CATÁLOGO ---

    # == CATEGORIAS
    path('panel/categorias/', views.lista_categorias_admin, name='lista_categorias_admin'),
    path('panel/categorias/crear/', views.crear_categoria, name='crear_categoria'),
    path('panel/categorias/eliminar/<int:categoria_id>/', views.eliminar_categoria, name='eliminar_categoria'),
    path('panel/categorias/editar/<int:categoria_id>/', views.editar_categoria, name='editar_categoria'),
    # == PRODUCTO
    # Productos sin categoriaa
    path('panel/catalogo/', views.lista_productos_admin, name='lista_productos_admin'),
    # Productos con categoría
    path('panel/catalogo/categoria/<int:categoria_id>/', views.lista_productos_admin, name='lista_productos_por_categoria'),
    path('panel/catalogo/crear/', views.crear_producto, name='crear_producto'),
    path('panel/catalogo/editar/<int:producto_id>/', views.editar_producto, name='editar_producto'),
    path('panel/catalogo/eliminar/<int:producto_id>/', views.eliminar_producto, name='eliminar_producto'),
    # == VARIANTES
    path('panel/catalogo/<int:producto_id>/variantes/', views.gestionar_variantes, name='gestionar_variantes'),
    path('panel/catalogo/variantes/eliminar/<int:variante_id>/', views.eliminar_variante, name='eliminar_variante'),
    path('panel/catalogo/variante/editar/<int:variante_id>/', views.editar_variante, name='editar_variante'),
    path('panel/catalogo/variante/<int:variante_id>/imagenes/', views.gestionar_imagenes_variante, name='gestionar_imagenes_variante'),
    path('panel/catalogo/imagen/eliminar/<int:imagen_id>/', views.eliminar_imagen_variante, name='eliminar_imagen_variante'),
]