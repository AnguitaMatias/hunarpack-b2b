import json
from django.http import JsonResponse
from django.shortcuts import render
from .models import Producto

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