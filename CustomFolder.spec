# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\cesiy\\Desktop\\custom_folder\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\cesiy\\Desktop\\custom_folder\\folder.png', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt6.QtWebEngineWidgets', 'PyQt6.QtWebEngineCore', 'PyQt6.QtWebEngine', 'PyQt6.QtNetwork', 'PyQt6.QtQml', 'PyQt6.QtQuick', 'PyQt6.QtBluetooth', 'PyQt6.QtMultimedia', 'PyQt6.QtSvg', 'PyQt6.QtOpenGL', 'PyQt6.QtPositioning', 'PyQt6.QtCharts', 'PyQt6.Qt3DCore', 'PyQt6.Qt3DExtras', 'PyQt6.Qt3DInput', 'PyQt6.Qt3DLogic', 'PyQt6.Qt3DRender', 'json', 'math', 'time'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='CustomFolder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
