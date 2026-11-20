#!/usr/bin/env bash

set -o errexit

# Instalación de dependencias
pip install -r requirements.txt

# Recopilación de archivos estáticos
python manage.py collectstatic --no-input

# Aplicar migraciones a la base de datos
python manage.py migrate