[app]
title = PLU App
package.name = pluapp
package.domain = org.tuniche
version = 0.1

# Tu proyecto está en la raíz del repo
source.dir = .
# Incluye CSV y recursos
source.include_exts = py,kv,png,jpg,jpeg,csv,ttf

# Requisitos
# - et_xmlfile es dependencia de openpyxl
requirements = python3,kivy,pillow,openpyxl,et_xmlfile

# Pantalla vertical
orientation = portrait

# (Opcional) ícono si existe en el repo
# Asegúrate que el archivo exista: icon.png
icon.filename = icon.png

# Android
android.api = 33
android.minapi = 24
android.archs = arm64-v8a

# CLAVE para GitHub Actions: aceptar licencias sin pregunta
android.accept_sdk_license = True

# Mejor logs si falla
log_level = 2

# Para evitar problemas de permisos, NO pedimos nada extra.
# (si después quieres guardar en /Download se agregan permisos)
# android.permissions =

# (Opcional) Si quieres que el csv quede dentro del APK como asset
# (normalmente con source.include_exts basta)
# android.assets = plu_catalogo.csv
