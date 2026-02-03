[app]
title = PLU App
package.name = pluapp
package.domain = org.tuniche
version = 0.1

source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,csv

requirements = python3,kivy,openpyxl,et_xmlfile,plyer,pyjnius

orientation = all

icon.filename = icon.png


# Android
android.api = 33
android.minapi = 24
android.archs = arm64-v8a

# ✅ para GitHub Actions (licencias sin pregunta)
android.accept_sdk_license = True

# Logs
log_level = 2
