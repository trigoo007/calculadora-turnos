# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['calculadora_app.py'],
    pathex=[],
    binaries=[],
    datas=[('/Users/rodrigomunoz/Calculadora/ui', 'ui'), ('/Users/rodrigomunoz/Calculadora/csv', 'csv'), ('/Users/rodrigomunoz/Calculadora/conocimiento', 'conocimiento'), ('/Users/rodrigomunoz/Calculadora/recursos', 'recursos'), ('/Users/rodrigomunoz/Calculadora/TIMELINE.md', '.'), ('/Users/rodrigomunoz/Calculadora/README.md', '.'), ('/Users/rodrigomunoz/Calculadora/README_INSTALACION.md', '.'), ('/Users/rodrigomunoz/Calculadora/CLAUDE.md', '.')],
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
    [],
    exclude_binaries=True,
    name='CalculadoraTurnos',
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
    name='CalculadoraTurnos',
)
app = BUNDLE(
    coll,
    name='CalculadoraTurnos.app',
    icon=None,
    bundle_identifier=None,
)
