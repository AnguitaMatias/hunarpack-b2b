/* Script para gestionar el carrito de compras */
document.addEventListener('DOMContentLoaded', () =>{
    const botonesAgregar = document.querySelectorAll('.btn-agregar');

    // Se lee el Token CSRF desde la etiqueta meta.
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    // Se agrega un evento de clic a cada botón.
    botonesAgregar.forEach(boton =>{
        boton.addEventListener('click', function(){
            const productoId = this.dataset.id;

            fetch('api/carrito/agregar/',{
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken //Aquí se hace la inyección del Token CSRF
                },
                body: JSON.stringify({'producto_id': productoId})
            })
            .then(response => response.json())
            .then(data => {
                if(data.status === 'ok') {
                    document.getElementById('contador-carrito').innerText = data.total_productos;

                    const btnOriginal = this.innerText;
                    this.innerText = '¡Agregado!';
                    this.classList.replace('btn-primary', 'btn-success');

                    setTimeout(() => {
                        this.innerText = btnOriginal;
                        this.classList.replace('btn-success', 'btn-primary');
                    },1000);
                } else if (data.status === 'sin_stock') {
                    // Manejo de quiebre.
                    const btnOriginal = this.innerText;
                    this.innerText = 'Stock Insuficiente';
                    this.classList.remove('btn-primary');
                    this.clasList.add('btn-danger');

                    // alerta al usuario
                    alert(data.mensaje);

                    // Restauramos el botón pasados 2 segundos
                    setTimeout(() =>{
                        this.innerText = btnOriginal;
                        this.classList.remove('btn-danger');
                        this.classList.add('btn-primary');
                    }, 2000);
                }
            });
        });
    });

    // Lógica de los botones +/- del resumen del carrito
    const botonesActualizar = document.querySelectorAll('.btn-actualizar');

    botonesActualizar.forEach(boton => {
        boton.addEventListener('click', function() {
            const productoId= this.dataset.id;
            const accion = this.dataset.accion;

            fetch('/api/carrito/actualizar/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    'producto_id': productoId,
                    'accion': accion
                })
            })
            .then(response => response.json())
            .then(data => {
                if(data.status === 'ok'){
                    document.getElementById('contador-carrito').innerText = data.total_productos;

                    if(data.nueva_cantidad === 0) {
                        // Si la cantidad es 0, la fila desaparece con un efecto
                        const fila = document.getElementById(`fila-${productoId}`);
                        fila.style.transition = "opacity 0.3s";
                        fila.style.opacity = "0";
                        setTimeout(() => fila.remove(), 300);

                        //Si el carro queda vacío, se recarga la página y muestra el mensaje personalizado
                        if(data.total_productos === 0) {
                            setTimeout(() => window.location.reload(), 350);
                        }
                    } else {
                        // Si la cantidad no es 0, se actualizan los números en pantalla
                        document.getElementById(`cantidad-${productoId}`).innerText = data.nueva_cantidad;
                        document.getElementById(`subtotal-${productoId}`).innerText = data.nuevo_subtotal;
                    }
                    // Se actualiza el total de la cotización
                    document.getElementById('total-cotizacion').innerText = data.total_cotizacion;

                } else if(data.status === 'sin_stock') {
                    alert(data.mensaje);
                }
            });
        });
    });

    //Lógica para el botón eliminar
    const botonesEliminar = document.querySelectorAll('.btn-eliminar');

    botonesEliminar.forEach(boton => {
        boton.addEventListener('click', function() {
            const productoId = this.dataset.id;

            fetch('/api/carrito/actualizar/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    'producto_id': productoId,
                    'accion': 'eliminar'
                })
            })
            .then(response => response.json())
            .then(data => {
                if(data.status === 'ok') {
                    document.getElementById('contador-carrito').innerText = data.total_productos;

                    const fila = document.getElementById(`fila-${productoId}`);
                    fila.style.transition = "opacity 0.3s";
                    fila.style.opacity = "0";
                    setTimeout(() => fila.remove(), 300);
                    
                    if(data.total_productos === 0) {
                        setTimeout(() => window.location.reload(), 350);
                    } else {
                        document.getElementById('total-cotizacion').innerText = data.total_cotizacion;
                    }
                }
            });
        });
    });

});