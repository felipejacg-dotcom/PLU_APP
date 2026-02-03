[app]
title = PLU App
package.name = pluapp
package.domain = org.tuniche
version = 0.1

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,csv

requirements = python3,kivy,pillow,openpyxl

orientation = portrait

android.api = 33
android.minapi = 24
android.archs = arm64-v8a

# Recomendado para ver logs si algo falla
log_level = 2
