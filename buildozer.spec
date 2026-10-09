[app]
title = ROM Translator GBA
package.name = romtranslatorgba
package.domain = org.pbkcenter
source.dir = .
source.include_exts = py,png,jpg,kv,json,ttf,txt
version = 0.1.0
requirements = python3,kivy,pillow,androidstorage4kivy
orientation = portrait
fullscreen = 0

android.api = 35
android.minapi = 23
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.allow_backup = False
android.private_storage = True

[buildozer]
log_level = 2
warn_on_root = 1
