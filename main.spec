# -*- mode: python ; coding: utf-8 -*-
# Build:  pyinstaller main.spec
# Output: dist/DigitalDoppelgangerTrap/DigitalDoppelgangerTrap.exe  (on Windows)
#
# Nmap is NOT bundled (its license/size make that messy for a hackathon build).
# The app looks for nmap on PATH, at the default Windows install locations, or at
# NMAP_PATH. Tell users: install Nmap from https://nmap.org/download.html and keep
# "Add to PATH" ticked during setup.

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[('templates', 'templates')],
    hiddenimports=['user_agents', 'webview'],
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
    name='DigitalDoppelgangerTrap',
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
