import json
import io
import random

from .forms import RegistroClienteForm
from .models import Producto, Categoria, Cotizacion, DetalleCotizacion, ReservarStock, VarianteProducto, ImagenVariante
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth import logout, login as auth_login
from django.contrib.auth.views import PasswordChangeView
from django.core.mail import send_mail, EmailMessage
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.utils import timezone
from datetime import timedelta
from xhtml2pdf import pisa

# -- LANDING --
def landing_page(request):
   # Se filtran productos con una variante al menos qeu tenga stock
   # .distinct() para evitar duplicidad de variantes del mismo producto

   productos_destacados = Producto.objects.filter(
       variantes__stock_actual__gt=0
   ).distinct().order_by('?')[:3]

   return render(request, 'catalogo/client/landing_page.html', {
       'productos_destacados': productos_destacados
   })

# -- VISTA DE PRODUCTOS --
def lista_categorias(request):
    categorias = Categoria.objects.all()
    query = request.GET.get('q')

    if query:
        productos = Producto.objects.filter(
            Q(nombre__icontains=query)  |
            Q(descripcion__icontains=query) |
            Q(variantes__codigo__icontains=query)
        ).distinct()

        return render(request, 'catalogo/client/lista_productos.html', {
            'productos': productos,
            'categorias': categorias,
            'query': query,
            'categoria_actual': None,
            'total_productos': sum(request.session.get('carrito', {}).values())
        })
    return render(request, 'catalogo/client/lista_categorias.html', {
        'categorias': categorias
    })

def lista_productos(request, categoria_id):
    categoria_actual = get_object_or_404(Categoria, id=categoria_id)
    productos = Producto.objects.filter(categoria=categoria_actual).prefetch_related('variantes')
    
    query = request.GET.get('q')
    if query:
        productos = Producto.objects.filter(
            Q(nombre__icontains=query)  |
            Q(descripcion__icontains=query) |
            Q(variantes__codigo__icontains=query)
        ).distinct()
      
    # Se revisa el carro en la sesión, si no existe, se crea uno diccionario vacío
    carrito = request.session.get('carrito', {})
    # Se calcula las cantidades de productos en el carro
    total_productos = sum(carrito.values())

    # Paso 4. Renderizado del html
    return render(request, 'catalogo/client/lista_productos.html', {
        'productos': productos,
        'categorias': Categoria.objects.all(),
        'categoria_actual': categoria_actual,
        'query': query,
        'total_productos': total_productos
    })

def detalle_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    variantes = producto.variantes.all()

    return render(request, 'catalogo/client/detalle_producto.html', {
        'producto': producto,
        'variantes': variantes
    })

# -- LÓGICA RESERVA DE STOCK --
def obtener_stock_disponible(variante, session_key_actual):
    # Paso 1. Se calcula cuánto está reservado en otro carritos en la última hora
    limite_tiempo = timezone.now() - timedelta(hours=1)
    reservas_ajenas = ReservarStock.objects.filter(
        variante=variante,
        fecha_creacion__gte=limite_tiempo
    ).exclude(session_key=session_key_actual)

    cantidad_reservada_otros = sum(r.cantidad for r in reservas_ajenas)

    # Paso 2. El stock disponible es el real menos el de los otros
    return variante.stock_actual - cantidad_reservada_otros

def actualizar_reserva(request, variante, cantidad_nueva):
    # Crea o actualiza la reserva del usuario actual
    if not request.session.session_key:
        request.session.create()

    if cantidad_nueva <= 0:
        ReservarStock.objects.filter(session_key=request.session.session_key, variante=variante).delete()
    else:
        ReservarStock.objects.update_or_create(
            session_key=request.session.session_key,
            variante=variante,
            defaults={'cantidad': cantidad_nueva}
        )

# -- LÓGICA PARA EL CARRO (AGREGAR, RESUMEN Y ACTUALIZAR) --
def agregar_al_carrito(request):
    if request.method == 'POST':
        #Comprobamos los datos que envió JS
        data = json.loads(request.body)
        variante_id = str(data.get('variante_id'))

        # Paso 1. Se valida el producto en la BD para consultar el stock actual
        try:
            variante = VarianteProducto.objects.get(id=variante_id)
        except Producto.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Variante no encontrada'})

        # Si no hay carro en la sesión, se crea uno vacío
        if 'carrito' not in request.session:
            request.session['carrito'] = {}
        carrito = request.session['carrito']
        cantidad_actual_carro = carrito.get(variante_id, 0)

        # validación contra stock comprometido
        stock_disponible = obtener_stock_disponible(variante, request.session.session_key)

        # Paso 2. Se valida que la cantidad en el carro no sobrepase el stock disponible.
        if cantidad_actual_carro + 1 > stock_disponible:
            return JsonResponse({
                'status': 'sin_stock',
                'mensaje': f'No puedes agregar más. Solo quedan {stock_disponible} unidades disponibles (otras están en carritos de otros clientes).'
            })

        # Paso 3. Si hay stock, se agrega al carro.
        carrito[variante_id] = cantidad_actual_carro + 1
        request.session.modified = True

        # Paso 4. Se actualiza la tabla de reservas en la BD
        actualizar_reserva(request, variante, carrito[variante_id])

        # Se calcula cuantos productos hay en total en el carro
        total_productos = sum(carrito.values())

        # Se devuelve una respuesta JSON confirmando el éxito y el total de productos.
        return JsonResponse({'status': 'ok', 'total_productos': total_productos})

    return JsonResponse({'status': 'error'}, status=400)

def resumen_carrito(request):
    #Se obtiene el carro de la sesión, si no existe, se crea uno diccionario vacío
    carrito = request.session.get('carrito', {})
    productos_carrito = []

    # Se obtienen todo los IDs del carrito
    ids_en_carrito = list(carrito.keys())

    # Se buscan los que realmente están en la BD
    variantes_reales = VarianteProducto.objects.filter(id__in=ids_en_carrito).values_list('id', flat=True)
    ids_validos = set(str(v) for v in variantes_reales)

    # Se dejan solo los IDs que sí existen en la BD
    carrito_limpio = {k: v for k, v in carrito.items() if k in ids_validos}

    if carrito_limpio != carrito:
        request.session['carrito'] = carrito_limpio
        request.session.modified= True
    
    total_productos = sum(carrito_limpio.values())

    #Iteracion sobre el carro temporal (producto_id: cantidad)
    for variante_id, cantidad in carrito_limpio.items():
        try:
            #Se busca el item real en la bd.
            variante = VarianteProducto.objects.get(id=variante_id)
            #Se arma un paquete con la info lista para la tabla (db).
            productos_carrito.append({
                'variante': variante,
                'cantidad': cantidad,
            })
        except VarianteProducto.DoesNotExist:
            #Si el producto fue borrado de la BD mientras esta en el carro lo ignora.
            pass

    return render(request, 'catalogo/client/resumen_carrito.html', {
        'productos_carrito': productos_carrito,
        'total_productos': total_productos
    })

def actualizar_carrito(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        variante_id = str(data.get('variante_id'))
        accion = data.get('accion')

        try:
            variante = VarianteProducto.objects.get(id=variante_id)
        except VarianteProducto.DoesNotExist:
            return JsonResponse({'status': 'error', 'mensaje': 'Variante no encontrada' })

        carrito = request.session.get('carrito', {})

        if variante_id in carrito:
            if accion == 'sumar':
                stock_disponible = obtener_stock_disponible(variante, request.session.session_key)
                if carrito[variante_id] + 1 > stock_disponible:
                    return JsonResponse({'status': 'sin_stock', 'mensaje': f'Stock máximo alcanzado. Quedan {stock_disponible}.'})
                carrito[variante_id] += 1

            elif accion == 'restar':
                if carrito[variante_id] > 1:
                    carrito[variante_id] -= 1
                else:
                    del carrito[variante_id]
                    
            elif accion == 'eliminar':
                del carrito[variante_id]
                
            elif accion == 'fijar':
                nueva_cant = int(data.get('cantidad', 1))
            
                stock_disponible = obtener_stock_disponible(variante, request.session.session_key)
                if nueva_cant > stock_disponible:
                    return JsonResponse({
                        'status': 'sin_stock',
                        'mensaje': f'Solo tenemos {stock_disponible} unidades disponibles (algunas están reservadas por otros clientes)',
                        'cantidad_corregida': carrito[variante_id]
                    })
                elif nueva_cant < 1:
                    del carrito[variante_id]
                else:
                    carrito[variante_id] = nueva_cant

        request.session.modified = True

        total_productos = sum(carrito.values())
        nueva_cantidad = carrito.get(variante_id, 0)
        
        # Actualizamos la reserva en la BD con la nueva cantidad (si es 0, la borra)
        actualizar_reserva(request, variante, nueva_cantidad)

        return JsonResponse({
            'status': 'ok',
            'nueva_cantidad': nueva_cantidad,
            'total_productos': total_productos
        })
    return JsonResponse({'status': 'error'}, status=400)

# -- LÓGICA PARA LAS COTIZACIONES --
@login_required(login_url='/login/')
def repetir_cotizacion(request, cotizacion_id):
    # Se recupera la cotización antigua (comprobando que le pertenece al usuario)
    cotizacion_antigua = get_object_or_404(Cotizacion, id=cotizacion_id, usuario=request.user)

    # Se recupera el carro actual de la sesión (se creará si no existe)
    carrito = request.session.get('carrito', {})

    # Se vacía el carro actual para evitar errores
    carrito.clear()

    # Se itera sobre los productos de la cotización antigua y se pasan al carro actual.
    for detalle in cotizacion_antigua.detalles.all():
        variante_id = str(detalle.variante.id)
        cantidad = detalle.cantidad

        # Comprobamos stock
        if cantidad > detalle.variante.stock_actual:
            cantidad = detalle.variante.stock_actual

        if cantidad > 0:
            carrito[variante_id] = cantidad

    # Se guarda el carro actual de la sesión.
    request.session['carrito'] = carrito
    request.session.modified = True

    messages.success(request, f"¡Cotización #{cotizacion_antigua.id} clonada! Se han cargado los productos disponibles de esta a tu carrito.")

    return redirect('resumen_carrito')

@transaction.atomic
def procesar_cotizacion(request):
    if request.method == 'POST':
        carrito = request.session.get('carrito', {})

        # Se compurbea que no se mande un carro vacío por la URL
        if not carrito:
            messages.error(request, "Tu carrito está vacío.")
            return redirect('lista_categorias')

        # Paso 1. Se crea el registro maestro "La cotización"
        cotizacion = Cotizacion.objects.create(
            usuario=request.user if request.user.is_authenticated else None,
            empresa=request.POST.get('empresa'),
            rut_empresa=request.POST.get('rut_empresa'),
            nombre_contacto=request.POST.get('nombre_contacto'),
            telefono=request.POST.get('telefono'),
            email=request.POST.get('email'),
            mensaje=request.POST.get('mensaje')
        )

        total_cotizacion = 0

        # Paso 2. Se intera sobre los items del carro para crear los "Detalles"
        for variante_id, cantidad in carrito.items():
            try:
                variante = VarianteProducto.objects.get(id=variante_id)

                # Comprobación del stock antes de confirmar en caso de que algun otro cliente 
                # compró mientras llenaba el formulario
                if cantidad > variante.stock_actual:
                    messages.error(request, f"Los sentimos, no hay stock suficiente de {variante.nombre_variante}")
                    cotizacion.delete()
                    return redirect('resumen_carrito')

                # Creación del detalle
                DetalleCotizacion.objects.create(
                    cotizacion=cotizacion,
                    variante=variante,
                    precio_unitario=0,
                    cantidad=cantidad,
                    subtotal=0
                )

                # Paso 3. Regla Crítica: descontar el stock real de la bodega
                variante.stock_actual -= cantidad
                variante.save()

            except VarianteProducto.DoesNotExist:
                pass

        # Paso 4. Actualizar el total en la cotización maestra
        cotizacion.total = 0
        cotizacion.save()

        # -- Envío del correo electronico --
        asunto = F"Confirmación de Cotización #{cotizacion.id} - HunarPack B2B"
        mensaje = f"""
        Hola {cotizacion.nombre_contacto},

        Hemos recibido tu solicitud de cotización para la empresa {cotizacion.empresa}.

        Resumen de la solicitud:
        - N° de Cotización: {cotizacion.id}

        Nuestro equipo de ventas revisará el inventario y se pondrá en contacto contigo a la brevedad.

        Gracias por preferir HunarPack.        
        """

        #Función para le envío y notificación el cliente
        #Asunto, mensaje texto, remitente, [destinatario]
        send_mail(
            asunto,
            mensaje,
            settings.DEFAULT_FROM_EMAIL,
            [cotizacion.email],
            fail_silently=False,
        )

        # Notificación al staff
        staff_emails = list(
            User.objects.filter(is_staff=True, is_active=True)
            .exclude(email='')
            .values_list('email', flat=True)
        )

        if staff_emails:
            panel_url = request.build_absolute_uri('/panel/')
            asunto_staff = f"Nueva Solicitud #{cotizacion.id} - {cotizacion.empresa}"
            cuerpo_staff = f"""Hola equipo,
Ha llegado una nueva solicitud de cotización al sistema.

Datos del cliente:
- Empresa: {cotizacion.empresa}
- RUT: {cotizacion.rut_empresa or 'No indicado'}
- Contacto: {cotizacion.nombre_contacto}
- Email: {cotizacion.email}
- Teléfono: {cotizacion.telefono}

N° de solicitud: #{cotizacion.id}
Productos solicitados: {cotizacion.detalles.count()}

Ingresa al panel para asignar precios y responder:
{panel_url}

Saludos,
Sistema HunarPack B2B
"""
            send_mail(
                asunto_staff,
                cuerpo_staff,
                settings.DEFAULT_FROM_EMAIL,
                staff_emails,
                fail_silently=True,
            )
        # -----------------------------------------------

        # Paso 5. Vaciar (destruir) el carrito temporal de la sesión
        del request.session['carrito']
        ReservarStock.objects.filter(session_key=request.session.session_key).delete()
        request.session.modified = True

        # Paso 6. Confirmar exito y redirigir a inicio
        messages.success(request, f"¡Su cotización se envió exitosamente!. Nos pondremos en contacto pronto.")
        return redirect('lista_categorias')

    return redirect('lista_categorias')

@staff_member_required
def generar_pdf_cotizacion(request, cotizacion_id):
    # Recuperamos la cotización del cliente desde la bd
    try:
        cotizacion = Cotizacion.objects.get(id=cotizacion_id)
    except Cotizacion.DoesNotExist:
        return HttpResponse("La cotización no existe.", status=404)

    # Pasamos los datos de la cotización a la plantilla HTML
    template = get_template('catalogo/pdf/pdf_cotizacion.html')
    context = {'cotizacion': cotizacion}
    html = template.render(context)

    # La respuesta se prepara como un archivo PDF descargable
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Cotizacion_Hunarpack_{cotizacion.id}.pdf"'

    # Se convierte el HTML a PDF
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Hubo un error al generar el PDF', status=500)

    return response

# -- INTERFAZ CLIENTES --
@login_required(login_url='/login/')
def mi_historial(request):
    # Se recuperan las id (cotizaciones) asociadas al usuario actua
    cotizaciones = Cotizacion.objects.filter(usuario=request.user).order_by('-fecha_creacion')

    return render(request, 'catalogo/client/mi_historial.html', {
        'cotizaciones': cotizaciones
    })

def salir(request):
    logout(request)
    messages.success(request, "Has cerrado sesión exitosamente.")
    return redirect('lista_categorias')

def registro(request):
    if request.method == 'POST':
        form = RegistroClienteForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            auth_login(request, usuario) # Inicia sesión automáticamente después del registro.
            nombre_bienvenida = usuario.first_name or usuario.username 
            messages.success(request, f"¡Te damos la bienvenida, {nombre_bienvenida}! Tu cuenta ha sido creada exitosamente.")
            return redirect('lista_categorias')
    else:
        form = RegistroClienteForm()

    return render(request, 'catalogo/auth/registro.html', {'form': form})

@login_required(login_url='/login/')
def mi_perfil(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        nuevo_email = request.POST.get('email', user.email).strip().lower()

        # Se comprueba que el correo no este registrado en otra cuenta
        if User.objects.filter(email__iexact=nuevo_email).exclude(id=user.id).exists():
            messages.error(request, "El correo electrónico ingresado ya está en uso por otra cuenta.")
        else:
            user.email = nuevo_email
            user.save()
            messages.success(request, "Tus datos personales han sido actualizados exitosamente.")
            return redirect('mi_perfil')
    return render(request, 'catalogo/client/mi_perfil.html')

class CambiarContrasena(PasswordChangeView):
    template_name = 'catalogo/auth/cambiar_contrasena.html'
    success_url = reverse_lazy('lista_productos')

    def form_valid(self, form):
        messages.success(self.request, "¡Tu contraseña ha sido actualizada exitosamente!")

        return super().form_valid(form)

# DASHBOARD (STAFF / ADMIN)
@staff_member_required(login_url='/login/')
def dashboard(request):
    cotizaciones_pendientes = Cotizacion.objects.filter(estado__in=['PENDIENTE', 'EN_REVISION']).order_by('-fecha_creacion')
    cotizaciones_respondidas = Cotizacion.objects.filter(estado='RESPONDIDA').order_by('-fecha_creacion')

    contexto = {
        'pendientes': cotizaciones_pendientes,
        'respondidas': cotizaciones_respondidas,
        'total_pendientes': cotizaciones_pendientes.count(),
    }

    return render(request, 'catalogo/admin_panel/dashboard.html', contexto)

@staff_member_required(login_url='/login/')
def fijar_precios_cotizacion(request, cotizacion_id):
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id)
    detalles = cotizacion.detalles.all()

    if request.method == 'POST':
        subtotal_neto_general = 0
        descuento_total_general = 0

        for detalle in detalles:
            precio_ingresado = request.POST.get(f'precio_{detalle.id}')
            dcto_ingresado = request.POST.get(f'descuento_{detalle.id}', 0)

            if precio_ingresado and precio_ingresado.isdigit():
                precio_neto = int(precio_ingresado)
                dcto_porcentaje = int(dcto_ingresado) if str(dcto_ingresado).isdigit() else 0

                detalle.precio_unitario = precio_neto
                detalle.porcentaje_descuento = dcto_porcentaje

                subtotal_linea_bruto = precio_neto * detalle.cantidad
                monto_descuento_linea = subtotal_linea_bruto * (dcto_porcentaje / 100)
                subtotal_linea_neto = subtotal_linea_bruto - monto_descuento_linea

                detalle.subtotal = int(subtotal_linea_neto)
                detalle.save()

                subtotal_neto_general += int(subtotal_linea_neto)
                descuento_total_general += int(monto_descuento_linea)

        # Calculos globales de la cotización
        cotizacion.subtotal_neto = subtotal_neto_general
        cotizacion.descuento_total = descuento_total_general
        cotizacion.iva = int(subtotal_neto_general * 0.19)
        cotizacion.total = cotizacion.subtotal_neto + cotizacion.iva

        # Se asigna a ejecutivo y cambiamos el estado
        cotizacion.ejecutivo = request.user
        cotizacion.estado = 'RESPONDIDA'
        cotizacion.save()

        # Creación del PDF y envío por correo
        #-------------------------------------

        # Paso 1. Renderizado en HTML del PDF
        template = get_template('catalogo/pdf/pdf_cotizacion.html')
        html = template.render({'cotizacion': cotizacion})

        # Paso 2. Se crea un buffer de memoria para el PDF
        pdf_buffer = io.BytesIO()
        pisa_status = pisa.CreatePDF(html, dest=pdf_buffer)

        if not pisa_status.err:
            # se retorna al ainicio del buffer para leerlo
            pdf_buffer.seek(0)

            # Paso 3. Se envía el correo al cliente con el PDF adjunto.
            asunto_cliente = f"Cotización N° {cotizacion.id} - HunarPack B2B"
            nombre_ejecutivo = f"{cotizacion.ejecutivo.first_name} {cotizacion.ejecutivo.last_name}".strip() or cotizacion.ejecutivo.username
            cuerpo_cliente = f"""Hola {cotizacion.nombre_contacto},
            
Adjunto encontrarás la cotización formal para {cotizacion.empresa}, con los valores vigentes solicitados.

Resumen:
- Cotizacion N°: {cotizacion.id}
- Total Final (IVA incluído): ${cotizacion.total}
- Días de validez: {cotizacion.dias_validez}

Si tienes alguna duda, puedes contactar a tu ejecutivo asignado: {nombre_ejecutivo}
{cotizacion.ejecutivo.email}

Gracias por preferir HunarPack.
"""
            email_cliente = EmailMessage(
                asunto_cliente,
                cuerpo_cliente,
                settings.DEFAULT_FROM_EMAIL,
                [cotizacion.email],
            )
            email_cliente.attach(
                f"Cotizacion_Hunarpack_{cotizacion.id}.pdf",
                pdf_buffer.getvalue(),
                'application/pdf'
            )
            email_cliente.send(fail_silently=False)


        messages.success(request, f"¡Cotización #{cotizacion.id} respondida y enviada al cliente por correo!")
        return redirect('dashboard')

    return render(request, 'catalogo/admin_panel/fijar_precios.html', {
        'cotizacion': cotizacion,
        'detalles': detalles
    })

@staff_member_required(login_url='/login/')
def eliminar_cotizacion(request, cotizacion_id):
    if request.method != 'POST':
        return redirect('dashboard')

    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id)

    # Solo se podrá eliminar si esta figura como Pendiente.
    if cotizacion.estado != 'PENDIENTE':
        messages.error(request, "Solo se pueden eliminar cotizaciones Pendientes.")
        return redirect('dashboard')

    with transaction.atomic():
        # Paso 1. Se devuelve el stock al inventario
        for detalle in cotizacion.detalles.all():
            variante = detalle.variante
            variante.stock_actual += detalle.cantidad
            variante.save()

        # Paso 2. Eliminar la cotización (incluido el detalle)
        cotizacion.delete()

    messages.success(request, f"La cotizacion #{cotizacion.id} fue eliminada y el stock devuelto a bodega.")
    return redirect('dashboard')

# FUNCIONES PARA AL ADMIN
def es_superadmin(user):
    return user.is_superuser

@user_passes_test(es_superadmin, login_url='/panel/')
def gestion_personal(request):
    if request.method == 'POST':
        # Tomamos los datos del formulario
        username = request.POST.get('username')
        email = request.POST.get('email')
        nombre = request.POST.get('first_name')
        apellido = request.POST.get('last_name')
        password = request.POST.get('password')

        # Comprobamos que el usuario no exista ya.
        if User.objects.filter(username=username).exists():
            messages.error(request, f"El usuario '{username}' ya está registrado. Intente con otro.")
        else:
            # Creación del usuario
            nuevo_staff = User.objects.create_user(username=username, email=email, password=password)
            nuevo_staff.first_name = nombre
            nuevo_staff.last_name = apellido
            nuevo_staff.is_staff = True
            nuevo_staff.save()
            messages.success(request, f"Ejecutivo {nombre} {apellido} creado exitosamente.")
        
        return redirect('gestion_personal')

    # Se recuperan todos los usuario que son staff (incluye al superadmin)
    equipo = User.objects.filter(is_staff=True).order_by('-is_superuser', 'first_name')

    return render(request, 'catalogo/admin_panel/gestion_personal.html', {'equipo': equipo})

@user_passes_test(es_superadmin, login_url='/panel/')
def editar_staff(request, user_id):
    integrante = get_object_or_404(User, id=user_id, is_staff=True)

    # Protección no permite editar el superusuario desde aquí
    if integrante.is_superuser:
        messages.error(request, "No puedes editar al superadministrador desde este panel.")
        return redirect('gestion_personal')

    if request.method == 'POST':
        integrante.first_name = request.POST.get('first_name', integrante.first_name)
        integrante.last_name = request.POST.get('last_name', integrante.last_name)
        integrante.email = request.POST.get('email', integrante.email)

        # Si se cambia la contraseña se resetea.
        nueva_password = request.POST.get('password')
        if nueva_password:
            integrante.set_password(nueva_password)
            messages.info(request, "La contraseña fue reseteada con éxito.")

        integrante.save()
        messages.success(request, f"Datos de {integrante.username} actualizados correctamente.")

        return redirect('gestion_personal')

    return render(request, 'catalogo/admin_panel/editar_staff.html', {'integrante': integrante})

@user_passes_test(es_superadmin, login_url='/panel/')
def eliminar_staff(request, user_id):
    # Por seguridad solo se reciben POST asi se evitan borrados vía URL
    if request.method != 'POST':
        return redirect('gestion_personal')

    integrante = get_object_or_404(User, id=user_id, is_staff=True)

    # Medidas de seguridad y protecciones críticas
    if integrante.is_superuser:
        messages.error(request, "No puedes eliminar al superadministrador.")
        return redirect('gestion_personal')

    if integrante == request.user:
        messages.error(request, "No peudes eliminar tu propia cuenta.")
        return redirect('gestion_personal')

    nombre = integrante.get_full_name() or integrante.username
    integrante.delete()
    messages.success(request, f"El ejecutivo {nombre} ha sido eliminado del equipo.")
    return redirect('gestion_personal')

@user_passes_test(es_superadmin, login_url='/panel/')
def simular_cotizacion(request):
    if request.method != 'POST':
        return redirect('dashboard')

    # Se usaran solo productos con stock disponible
    variantes_disponibles = list(VarianteProducto.objects.filter(stock_actual__gt=0))
    if not variantes_disponibles:
        messages.error(request, "No hay productos con stock disponibles para simular una cotización.")
        return redirect('dashboard')

    # Se eligen entre 1 y 3 productos al azar
    cantidad_productos = min(len(variantes_disponibles), random.randint(1, 3))
    variantes_elegidas = random.sample(variantes_disponibles, cantidad_productos)

    # Creación de la cotizacion simulada
    cotizacion =  Cotizacion.objects.create(
        usuario=request.user,
        empresa="Empresa Simulada SpA",
        rut_empresa="76.543.210-K",
        nombre_contacto="Contacto de Prueba",
        telefono="+56 9 1234 5678",
        email="simulacion@hunarpack.cl",
        mensaje="[SIMULACION] Esta cotización fue generada automáticamente para pruebas del sistema.",
        estado='PENDIENTE',
    )

    for variante in variantes_elegidas:
        cantidad = random.randint(1, min(5, variante.stock_actual))
        DetalleCotizacion.objects.create(
            cotizacion=cotizacion,
            variante=variante,
            cantidad=cantidad,
            precio_unitario=0,
            subtotal=0,
        )
        # Al ser simulación no se descuenta realmente del stock
    
    messages.success(
        request,
        f"Cotización simulada #{cotizacion.id} creada con {cantidad_productos} productos. Revisa la bandeja de pendientes."
    )
    return redirect('dashboard')



