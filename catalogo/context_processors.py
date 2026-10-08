def contador_carrito(request):
    # Carro de la sesión si hay, su no diccionario vacío
    carrito = request.session.get('carrito', {})

    # Se suman las cantidades
    total = sum(carrito.values())


    # Se retorna el diccionado, esta variable estará disponible en toda la web.
    return {'total_carrito_global': total}