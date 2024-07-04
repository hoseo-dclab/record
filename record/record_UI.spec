# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['record_UI.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\dclab\\Desktop\\solution\\record\\record_on.png', '.'), ('C:\\Users\\dclab\\Desktop\\solution\\record\\record_off.png', '.'), ('C:\\Users\\dclab\\Desktop\\solution\\record\\stop_on.png', '.'), ('C:\\Users\\dclab\\Desktop\\solution\\record\\stop_off.png', '.'), ('C:\\Users\\dclab\\Desktop\\solution\\record\\pause.png', '.')],
    hiddenimports=[],
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
    a.binaries,
    a.datas,
    [],
    name='record_UI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
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
