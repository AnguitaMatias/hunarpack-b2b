import json
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from .models import Producto, Categoria, Cotizacion, DetalleCotizacion
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, login as auth_login
from django.contrib.auth.forms import UserCreationForm

# Vista de productos
def lista_productos(request):
    # Se recuperan los productos de la bd
    productos = Producto.objects.all()
    # Se recuperan las categorías para el menú
    categorias = Categoria.objects.all()

    # Paso 1. Capturar lo que el usuario escribe en la URL (?q=caja&categoria=1)
    query = request.GET.get('q')
    categoria_id = request.GET.get('categoria')

    # Paso 2. Se aplica los filtros a la bd en caso de que se haya buscado algo.
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)

    # Q permite la bsuqueda en el nombre y en la descripcion de manera simultanea
    if query:
        productos = productos.filter(Q(nombre__icontains=query) | Q(descripcion__icontains=query))

    # Paso 3. Lógica del carrito        
    # Se revisa el carro en la sesión, si no existe, se crea uno diccionario vacío
    carrito = request.session.get('carrito', {})
    # Se calcula las cantidades de productos en el carro
    total_productos = sum(carrito.values())

    # Paso 4. Renderizado del html
    return render(request, 'catalogo/lista_productos.html', {
        'productos': productos,
        'categorias': categorias,
        'total_productos': total_productos,
        'query': query,
        'categoria_id': str(categoria_id) if categoria_id else '',
    })

# Logica para agregar al carro
def agregar_al_carrito(request):
    if request.method == 'POST':
        #Comprobamos los datos que envió JS
        data = json.loads(request.body)
        producto_id = str(data.get('producto_id'))

        # Paso 1. Se valida el producto en la BD para consultar el stock actual
        try:
            producto = Producto.objects.get(id=producto_id)
        except Producto.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Producto no encontrado'})

        # Si no hay carro en la sesión, se crea uno vacío
        if 'carrito' not in request.session:
            request.session['carrito'] = {}

        carrito = request.session['carrito']
        cantidad_actual_carro = carrito.get(producto_id, 0)

        # Paso 2. Se valida que la cantidad en el carro no sobrepase el stock disponible.
        if cantidad_actual_carro + 1 > producto.stock_actual:
            return JsonResponse({
                'status': 'sin_stock',
                'mensaje': f'Solo hay {producto.stock_actual} unidades disponibles.'
            })

        # Paso 3. Si hay stock, se agrega al carro.
        if producto_id in carrito:
            carrito[producto_id] += 1
        else:
            carrito[producto_id] = 1

        # Se guarda el carro actualizado en la sesión
        request.session.modified = True

        # Se calcula cuantos productos hay en total en el carro
        total_productos = sum(carrito.values())

        # Se devuelve una respuesta JSON confirmando el éxito y el total de productos.
        return JsonResponse({'status': 'ok', 'total_productos': total_productos})

    return JsonResponse({'status': 'error'}, status=400)

# Logica para resumen del carro
def resumen_carrito(request):
    #Se obtiene el carro de la sesión, si no existe, se crea uno diccionario vacío
    carrito = request.session.get('carrito', {})

    #Guardamos los datos para enviarlos al template.
    productos_carrito = []
    total_productos = sum(carrito.values())
    #Iteracion sobre el carro temporal (producto_id: cantidad)
    for producto_id, cantidad in carrito.items():
        try:
            #Se busca el item real en la bd.
            producto = Producto.objects.get(id=producto_id)
            #Se arma un paquete con la info lista para la tabla (db).
            productos_carrito.append({
                'producto': producto,
                'cantidad': cantidad,
            })
        except Producto.DoesNotExist:
            #Si el producto fue borrado de la BD mientras esta en el carro lo ignora.
            pass

    return render(request, 'catalogo/resumen_carrito.html', {
        'productos_carrito': productos_carrito,
        'total_productos': total_productos
    })

# API para actualizar el carrito
def actualizar_carrito(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        producto_id = str(data.get('producto_id'))
        accion = data.get('accion') # pudiendo ser sumar o restar del producto

        try:
            producto = Producto.objects.get(id=producto_id)
        except Producto.DoesNotExist:
            return JsonResponse({'status': 'error', 'mensaje': 'Producto no encontrado' })

        carrito = request.session.get('carrito',{})

        if producto_id in carrito:
            if accion == 'sumar':
                # Primero se comprueba que no supere el stock en bodega
                if carrito[producto_id] + 1 > producto.stock_actual:
                    return JsonResponse({'status': 'sin_stock', 'mensaje': f'Stock máximo alcanzado ({producto.stock_actual}).'})
                carrito[producto_id] += 1

            elif accion == 'restar':
                if carrito[producto_id] > 1:
                    carrito[producto_id] -= 1
                else: #en caso de que tenga solo 1, se elimina del carro
                    del carrito[producto_id]
            elif accion == 'eliminar':
                del carrito[producto_id]
            elif accion == 'fijar':
                nueva_cant = int(data.get('cantidad', 1))

                if nueva_cant > producto.stock_actual:
                    return JsonResponse({
                        'status': 'sin_stock',
                        'mensaje': f'Solo tenemos {producto.stock_actual} unidades disponibles',
                        'cantidad_corregida': carrito[producto_id] # se retorna el valor seguro anterior
                    })
                # Si ingresa 0 o menos se elimina
                elif nueva_cant < 1:
                    del carrito[producto_id]
                else:
                    carrito[producto_id] = nueva_cant

        request.session.modified = True

        # Se calcula nuevamente los totatels para enviarlos actualizados al template.
        total_productos = sum(carrito.values())
        nueva_cantidad = carrito.get(producto_id, 0)


        return JsonResponse({
            'status': 'ok',
            'nueva_cantidad': nueva_cantidad,
            'total_productos': total_productos
        })
    return JsonResponse({'status': 'error'}, status=400)

# Lógica para guardar y descontar stock
@transaction.atomic
def procesar_cotizacion(request):
    if request.method == 'POST':
        carrito = request.session.get('carrito', {})

        # Se compurbea que no se mande un carro vacío por la URL
        if not carrito:
            messages.error(request, "Tu carrito está vacíp.")
            return redirect('lista_productos')

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
        for producto_id, cantidad in carrito.items():
            try:
                producto = Producto.objects.get(id=producto_id)

                # Comprobación del stock antes de confirmar en caso de que algun otro cliente 
                # compró mientras llenaba el formulario
                if cantidad > producto.stock_actual:
                    messages.error(request, f"Los sentimos, no hay stock suficiente de {producto.nombre}")
                    cotizacion.delete()
                    return redirect('resumen_carrito')

                # Creación del detalle
                DetalleCotizacion.objects.create(
                    cotizacion=cotizacion,
                    producto=producto,
                    precio_unitario=0,
                    cantidad=cantidad,
                    subtotal=0
                )

                # Paso 3. Regla Crítica: descontar el stock real de la bodega
                producto.stock_actual -= cantidad
                producto.save()

            except Producto.DoesNotExist:
                pass

        # Paso 4. Actualizar el total en la cotización maestra
        cotizacion.total = 0
        cotizacion.save()

        # -- Envío del correo electronico -- (actualmente en desarrollo no olvidar)
        asunto = F"Confirmación de Cotización #{cotizacion.id} - HunarPack B2B"
        mensaje = f"""
        Hola {cotizacion.nombre_contacto},

        Hemos recibido tu solicitud de cotización para la empresa {cotizacion.empresa}.

        Resumen de la solicitud:
        - N° de Cotización: {cotizacion.id}

        Nuestro equipo de ventas revisará el inventario y se pondrá en contacto contigo a la brevedad.

        Gracias por preferir HunarPack.        
        """

        #Función para le envío
        #Asunto, mensaje texto, remitente, [destinatario]
        send_mail(
            asunto,
            mensaje,
            settings.DEFAULT_FROM_EMAIL,
            [cotizacion.email],
            fail_silently=False,
        )
        # -----------------------------------------------

        # Paso 5. Vaciar (destruir) el carrito temporal de la sesión
        del request.session['carrito']
        request.session.modified = True

        # Paso 6. Confirmar exito y redirigir a inicio (PROBAR ALGUNA PANTALLA DE "AGRADECIMIENTO" PENDIENTE)
        messages.success(request, f"¡Su cotización se envió exitosamente!. Nos pondremos en contacto pronto.")
        return redirect('lista_productos')

    return redirect('lista_productos')

# Lógica para la generación del PDF (limitada solo al staff y admin)
@staff_member_required
def generar_pdf_cotizacion(request, cotizacion_id):
    # Recuperamos la cotización del cliente desde la bd
    try:
        cotizacion = Cotizacion.objects.get(id=cotizacion_id)
    except Cotizacion.DoesNotExist:
        return HttpResponse("La cotización no existe.", status=404)

    # Pasamos los datos de la cotización a la plantilla HTML
    template = get_template('catalogo/pdf_cotizacion.html')
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

# Ingreso del Cliente (Login)
@login_required(login_url='/login/')
def mi_historial(request):
    # Se recuperan las id (cotizaciones) asociadas al usuario actua
    cotizaciones = Cotizacion.objects.filter(usuario=request.user).order_by('-fecha_creacion')

    return render(request, 'catalogo/mi_historial.html', {
        'cotizaciones': cotizaciones
    })

def salir(request):
    logout(request)
    messages.success(request, "Has cerrado sesión exitosamente.")
    return redirect('lista_productos')

def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            auth_login(request, usuario) # Inicia sesión automáticamente después del registro.
            messages.success(request, f"¡Te damos la bienvenida, {usuario.username}! Tu cuenta ha sido creada exitosamente.")
            return redirect('lista_productos')
    else:
        form =UserCreationForm()

    return render(request, 'catalogo/registro.html', {'form': form})