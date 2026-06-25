#!/usr/bin/env bash
# Render build script - Weapon Detection System (Server)
# Se ejecuta en cada deploy dentro de la red de Render, donde la BD sí conecta.
set -o errexit

pip install -r requirements.txt

# Crea las tablas en la base de datos PostgreSQL de Render (auth_user, etc.)
python manage.py migrate --no-input

# Archivos estáticos
python manage.py collectstatic --no-input
