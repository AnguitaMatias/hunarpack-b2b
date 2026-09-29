/* Script para gestionar el carrito de compras */
document.addEventListener('DOMContentLoaded', () =>{
    // -- Función de las notificaciones (Toast) --
    function mostrarToast(mensaje, tipo) {
        const toastElement = document.getElementById('sistemaToast');
        const toastMensaje = document.getElementById('toastMensaje');

        // Se quita cualquier color previo.
        toastElement.classList.remove('bg-success', 'bg-danger', 'bg-warning', 'text-dark');

        // Se asignarán colores de acuerdo al tipo de aviso
        if(tipo === 'error') {
            toastElement.classList.add('bg-danger');
        } else if (tipo === 'exito') {
            toastElement.classList.add('bg-success');
        } else if (tipo === 'advertencia') {
            toastElement.classList.add('bg-warning', 'text-dark');
        }

        // Se agrega el mensaje
        toastMensaje.innerText = mensaje;

        // Se lanza toast usando bootstrap (permanece durante 3 segundos)
        const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
        toast.show();
    }
    const botonesAgregar = document.querySelectorAll('.btn-agregar');
    // Se lee el Token CSRF desde la etiqueta meta.
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    // Se agrega un evento de clic a cada botón.
    botonesAgregar.forEach(boton =>{
        boton.addEventListener('click', function(){
            const productoId = this.dataset.id;
            const btnElement = this;
            
            const btnOriginal = btnElement.innerHTML;
            btnElement.disabled = true;
            btnElement.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Agregando...';
            
            fetch('/api/carrito/agregar/',{
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
                    // actualización del contador del carro
                    document.getElementById('contador-carrito').innerText = data.total_productos;
                    // Animación de éxito.
                    btnElement.innerHTML = '¡Agregago!';
                    btnElement.classList.replace('btn-primary', 'btn-success');
                    btnElement.disabled = false;

                    // Restauración al estado original del botón.
                    setTimeout(() => {
                        btnElement.innerHTML = btnOriginal;
                        btnElement.classList.replace('btn-success', 'btn-primary');
                    },1000);

                } else if (data.status === 'sin_stock') {
                    // Manejo de quiebre de stock.
                    btnElement.innerHTML = 'Stock Insuficiente';
                    btnElement.classList.remove('btn-primary');
                    btnElement.classList.add('btn-danger');
                    btnElement.disabled = false;

                    // alerta al usuario
                    mostrarToast(data.mensaje, 'error');

                    // Restauramos el botón pasados 2 segundos
                    setTimeout(() =>{
                        btnElement.innerHTML = btnOriginal;
                        btnElement.classList.remove('btn-danger');
                        btnElement.classList.add('btn-primary');
                    }, 2000);
                }
            })
            .catch(error => {
                // En caso de intermitencia de red, el botón vuelve al estado original
                btnElement.disabled = false;
                btnElement.innerHTML = btnOriginal
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
                        document.getElementById(`cantidad-${productoId}`).value = data.nueva_cantidad;
                        /* document.getElementById(`subtotal-${productoId}`).innerText = data.nuevo_subtotal; */
                    }
                    // Se actualiza el total de la cotización
                    /* document.getElementById('total-cotizacion').innerText = data.total_cotizacion; */

                } else if(data.status === 'sin_stock') {
                    mostrarToast(data.mensaje, 'error');
                }
            });
        });
    });

    // Lógica para el botón eliminar
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
                        /* document.getElementById('total-cotizacion').innerText = data.total_cotizacion; */
                    }
                }
            });
        });
    });

    // Lógica para el input manual en la cantidad
    const inputsCantidad = document.querySelectorAll('.input-cantidad');

    inputsCantidad.forEach(input =>{
        input.addEventListener('change', function () {
            const productoId = this.dataset.id;
            let nuevaCantidad = parseInt(this.value);

            // se fuerza 1 en caso de que borre todo o ponga una letra
            if (isNaN(nuevaCantidad) || nuevaCantidad < 1) {
                nuevaCantidad = 1;
                this.value = 1;
            }

            fetch('/api/carrito/actualizar/',{
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },

                body: JSON.stringify({
                    'producto_id': productoId,
                    'accion': 'fijar',
                    'cantidad': nuevaCantidad
                })
            })
            .then(response => response.json())
            .then(data => {
                if(data.status === 'ok') {
                    document.getElementById('contador-carrito').innerText = data.total_productos;
                    /* document.getElementById(`subtotal-${productoId}`).innerText = data.nuevo_subtotal;
                    document.getElementById('total-cotizacion').innerText = data.total_cotizacion; */
                } else if (data.status === 'sin_stock') {
                    mostrarToast(data.mensaje, 'error');
                    this.value = data.cantidad_corregida;
                }
            });
        });
    });

});