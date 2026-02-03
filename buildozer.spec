[app]
title = PLU APP
package.name = pluapp
package.domain = org.felipe

source.dir = .
source.include_exts = py,csv,png,jpg,kv


orientation = sensor

requirements = python3,kivy,openpyxl,et_xmlfile


android.api = 33
android.minapi = 24
android.archs = arm64-v8a


log_level = 2


android.accept_sdk_license = True
