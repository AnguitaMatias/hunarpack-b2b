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
                    this.cassList.remove('btn-primary');
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

});