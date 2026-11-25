# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('resources/locale/es/LC_MESSAGES/*.mo', 'resources/locale/es/LC_MESSAGES'),
        ('resources/locale/fr/LC_MESSAGES/*.mo', 'resources/locale/fr/LC_MESSAGES'),
        ('resources/locale/pt/LC_MESSAGES/*.mo', 'resources/locale/pt/LC_MESSAGES'),
        ('resources/images/*.png', 'resources/images'),
        ('resources/images/*.ico', 'resources/images'),
        ('resources/world_data/*.tif', 'resources/world_data')
    ],
    hiddenimports=['PIL._tkinter_finder'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Util_paisagem',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='utilpaisagem-appimage',
)
