# -*- mode: python ; coding: utf-8 -*-
# ============================================================
# SecurePasswordManager.spec — ملف بناء PyInstaller
# ينتج ملفًا تنفيذيًا واحدًا: dist/SecurePasswordManager.exe
#   - onefile: كل المكتبات وملفات الخطوط والأصول مضمّنة داخل EXE
#   - console=False: تطبيق رسومي بدون نافذة أوامر
#   - icon: assets/app_icon.ico
# ملاحظة: البناء يجب أن يُنفَّذ على Windows (لا يدعم PyInstaller
#          إنتاج ملفات Windows من Linux).
# ============================================================

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('fonts', 'fonts'),        # خط Noto Sans Arabic المرفق
        ('assets', 'assets'),      # شعار التطبيق وأيقونة EXE
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SecurePasswordManager',
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon='assets/app_icon.ico',
)
