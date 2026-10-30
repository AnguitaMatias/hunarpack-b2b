/* Script para gestionar el carrito de compras */
document.addEventListener('DOMContentLoaded', () => {
    
    // -- Función de las notificaciones (Toast) --
    function mostrarToast(mensaje, tipo) {
        const toastElement = document.getElementById('sistemaToast');
        const toastMensaje = document.getElementById('toastMensaje');
        if (!toastElement || !toastMensaje) return;

        toastElement.classList.remove('bg-success', 'bg-danger', 'bg-warning', 'text-dark');

        if (tipo === 'error') {
            toastElement.classList.add('bg-danger');
        } else if (tipo === 'exito') {
            toastElement.classList.add('bg-success');
        } else if (tipo === 'advertencia') {
            toastElement.classList.add('bg-warning', 'text-dark');
        }

        toastMensaje.innerText = mensaje;
        const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
        toast.show();
    }

    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    // -- 1. Botones de agregar al carro (Desde el catálogo) --
    const botonesAgregar = document.querySelectorAll('.btn-agregar');
    botonesAgregar.forEach(boton => {
        boton.addEventListener('click', function() {
            const varianteId = this.dataset.id;
            const btnElement = this;
            const btnOriginal = btnElement.innerHTML;
            
            btnElement.disabled = true;
            btnElement.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';
            
            fetch('/api/carrito/agregar/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify({ 'variante_id': varianteId })
            })
            .then(response => response.json())
            .then(data => {
                if(data.status === 'ok') {
                    document.getElementById('contador-carrito').innerText = data.total_productos;
                    btnElement.innerHTML = '¡Agregado!';
                    btnElement.classList.replace('btn-primary', 'btn-success');
                    setTimeout(() => {
                        btnElement.innerHTML = btnOriginal;
                        btnElement.classList.replace('btn-success', 'btn-primary');
                    }, 1000);
                } else if (data.status === 'sin_stock') {
                    mostrarToast(data.mensaje, 'error');
                    btnElement.innerHTML = 'Sin Stock';
                    setTimeout(() => { btnElement.innerHTML = btnOriginal; }, 2000);
                }
            })
            .catch(() => { btnElement.innerHTML = btnOriginal; })
            .finally(() => { btnElement.disabled = false; });
        });
    });

    // -- 2. Botones de + / - en el resumen del carrito --
    const botonesActualizar = document.querySelectorAll('.btn-actualizar');
    botonesActualizar.forEach(boton => {
        boton.addEventListener('click', function() {
            const varianteId = this.dataset.id;
            const accion = this.dataset.accion;

            fetch('/api/carrito/actualizar/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify({ 'variante_id': varianteId, 'accion': accion })
            })
            .then(response => response.json())
            .then(data => {
                if(data.status === 'ok') {
                    document.getElementById('contador-carrito').innerText = data.total_productos;

                    if(data.nueva_cantidad === 0) {
                        const fila = document.getElementById(`fila-${varianteId}`);
                        if(fila) {
                            fila.style.transition = "opacity 0.3s";
                            fila.style.opacity = "0";
                            setTimeout(() => fila.remove(), 300);
                        }
                        if(data.total_productos === 0) {
                            setTimeout(() => window.location.reload(), 350);
                        }
                    } else {
                        // Se actualiza el input con la nueva cantidad
                        const inputCantidad = document.getElementById(`cantidad-${varianteId}`);
                        if(inputCantidad) {
                            inputCantidad.value = data.nueva_cantidad;
                        }
                    }
                } else if(data.status === 'sin_stock') {
                    mostrarToast(data.mensaje, 'error');
                }
            })
            .catch(() => mostrarToast("Error de conexión", "error"));
        });
    });

    // -- 3. Botón Eliminar en el resumen del carrito --
    const botonesEliminar = document.querySelectorAll('.btn-eliminar');
    botonesEliminar.forEach(boton => {
        boton.addEventListener('click', function() {
            const varianteId = this.dataset.id;

            fetch('/api/carrito/actualizar/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify({ 'variante_id': varianteId, 'accion': 'eliminar' })
            })
            .then(response => response.json())
            .then(data => {
                if(data.status === 'ok') {
                    document.getElementById('contador-carrito').innerText = data.total_productos;
                    const fila = document.getElementById(`fila-${varianteId}`);
                    if(fila) {
                        fila.style.transition = "opacity 0.3s";
                        fila.style.opacity = "0";
                        setTimeout(() => fila.remove(), 300);
                    }
                    if(data.total_productos === 0) {
                        setTimeout(() => window.location.reload(), 350);
                    }
                }
            })
            .catch(() => mostrarToast("Error de conexión", "error"));
        });
    });

    // -- 4. Input manual de cantidad en el resumen del carrito --
    const inputsCantidad = document.querySelectorAll('.input-cantidad');
    inputsCantidad.forEach(input => {
        input.addEventListener('change', function () {
            const varianteId = this.dataset.id;
            let nuevaCantidad = parseInt(this.value);

            if (isNaN(nuevaCantidad) || nuevaCantidad < 1) {
                nuevaCantidad = 1;
                this.value = 1;
            }

            fetch('/api/carrito/actualizar/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify({ 'variante_id': varianteId, 'accion': 'fijar', 'cantidad': nuevaCantidad })
            })
            .then(response => response.json())
            .then(data => {
                if(data.status === 'ok') {
                    document.getElementById('contador-carrito').innerText = data.total_productos;
                } else if (data.status === 'sin_stock') {
                    mostrarToast(data.mensaje, 'error');
                    this.value = data.cantidad_corregida;
                }
            })
            .catch(() => mostrarToast("Error de conexión", "error"));
        });
    });

});