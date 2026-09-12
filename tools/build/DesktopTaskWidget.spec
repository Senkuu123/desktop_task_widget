# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

PROJECT_DIR = Path(SPECPATH).resolve().parents[1]

a = Analysis(
    [str(PROJECT_DIR / 'src' / 'main.py')],
    pathex=[str(PROJECT_DIR / 'src')],
    binaries=[],
    datas=[
        (str(PROJECT_DIR / 'src/resources/app_icon.ico'), '.'),
        (str(PROJECT_DIR / 'tools/build/version_info.txt'), '.'),
        (str(PROJECT_DIR / 'tools/build/dpi.manifest'), '.'),
        (str(PROJECT_DIR / 'src' / 'images_rc.py'), '.'),
    ],
    hiddenimports=['PyQt5.sip', 'ctypes', 'winreg', 'platform', 'sys', 'os', 'datetime', 'json', 're', 'images_rc', 'winotify'],
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
    name='DesktopTaskWidget',
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
    version=str(PROJECT_DIR / 'tools/build/version_info.txt'),
    manifest=str(PROJECT_DIR / 'tools/build/dpi.manifest'),
    icon=[str(PROJECT_DIR / 'src/resources/app_icon.ico')],
)
