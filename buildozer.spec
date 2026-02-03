[app]
title = PLU APP
package.name = pluapp
package.domain = org.felipe

source.dir = .
source.include_exts = py,csv,png,jpg,kv

# Importante: "all" NO existe. Usa portrait o landscape.
orientation = landscape

requirements = python3,kivy,openpyxl,et_xmlfile

# Si tu csv se llama así y está en la raíz del repo, queda dentro del APK.
# (Con include_exts también basta, pero esto ayuda a recordarlo)
# android.assets = plu_catalogo.csv

android.api = 33
android.minapi = 24
android.archs = arm64-v8a

# Logs más completos si vuelve a fallar:
log_level = 2

# Licencias automáticas (para GitHub Actions)
android.accept_sdk_license = True
