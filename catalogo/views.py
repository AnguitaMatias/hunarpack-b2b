import json
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Producto, Cotizacion, DetalleCotizacion

# Vista de productos
def lista_productos(request):
    #Se recuperan los productos de la bd de Supabase
    productos = Producto.objects.all()

    #Se revisa el carro en la sesión, si no existe, se crea uno diccionario vacío
    carrito = request.session.get('carrito', {})
    #Se calcula las cantidades de productos en el carro
    total_productos = sum(carrito.values())

    #Se rendenrizan en HTML
    return render(request, 'catalogo/lista_productos.html', {
        'productos': productos,
        'total_productos': total_productos
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
    total_cotizacion = 0
    total_productos = sum(carrito.values())
    #Iteracion sobre el carro temporal (producto_id: cantidad)
    for producto_id, cantidad in carrito.items():
        try:
            #Se busca el item real en la bd.
            producto = Producto.objects.get(id=producto_id)
            subtotal = producto.precio * cantidad
            total_cotizacion += subtotal

            #Se arma un paquete con la info lista para la tabla (db).
            productos_carrito.append({
                'producto': producto,
                'cantidad': cantidad,
                'subtotal': subtotal
            })
        except Producto.DoesNotExist:
            #Si el producto fue borrado de la BD mientras esta en el carro lo ignora.
            pass

    return render(request, 'catalogo/resumen_carrito.html', {
        'productos_carrito': productos_carrito,
        'total_cotizacion': total_cotizacion,
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

        request.session.modified = True

        # Se calcula nuevamente los totatels para enviarlos actualizados al template.
        total_productos = sum(carrito.values())
        nueva_cantidad = carrito.get(producto_id, 0)
        nuevo_subtotal = producto.precio * nueva_cantidad if nueva_cantidad > 0 else 0

        total_cotizacion = 0
        for pid, cant in carrito.items():
            try:
                p = Producto.objects.get(id=pid)
                total_cotizacion += p.precio * cant
            except Producto.DoesNotExist:
                pass

        return JsonResponse({
            'status': 'ok',
            'nueva_cantidad': nueva_cantidad,
            'nuevo_subtotal': nuevo_subtotal,
            'total_cotizacion': total_cotizacion,
            'total_productos': total_productos
        })
    return JsonResponse({'status': 'error'}, status=400)

# Lógica para guardar y descontar stock
def procesar_cotizacion(request):
    if request.method == 'POST':
        carrito = request.session.get('carrito', {})

        # Se compurbea que no se mande un carro vacío por la URL
        if not carrito:
            messages.error(request, "Tu carrito está vacíp.")
            return redirect('lista_productos')

        # Paso 1. Se crea el registro maestro "La cotización"
        cotizacion = Cotizacion.objects.create(
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

                subtotal = producto.precio * cantidad
                total_cotizacion += subtotal

                # Creación del detalle
                DetalleCotizacion.objects.create(
                    cotizacion=cotizacion,
                    producto=producto,
                    precio_unitario=producto.precio,
                    cantidad=cantidad,
                    subtotal=subtotal
                )

                # Paso 3. Regla Crítica: descontar el stock real de la bodega
                producto.stock_actual -= cantidad
                producto.save()

            except Producto.DoesNotExist:
                pass

        # Paso 4. Actualizar el total en la cotización maestra
        cotizacion.total = total_cotizacion
        cotizacion.save()

        # Paso 5. Vaciar (destruir) el carrito temporal de la sesión
        del request.session['carrito']
        request.session.modified = True

        # Paso 6. Confirmar exito y redirigir a inicio (PROBAR ALGUNA PANTALLA DE "AGRADECIMIENTO" PENDIENTE)
        messages.success(request, f"¡Su cotización se envió exitosamente! N° de Solicitud: {cotizacion.id}. Nos pondremos en contacto pronto.")
        return redirect('lista_productos')

    return redirect('lista_productos')