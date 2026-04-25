# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

block_cipher = None
try:
    project_root = Path(SPEC).resolve().parent  # type: ignore[name-defined]
except Exception:
    project_root = Path.cwd()

datas = []
generated_build_info = project_root / "build" / "build_info.json"
if generated_build_info.exists():
    datas.append((str(generated_build_info), "app/resources"))

a = Analysis(
    ["app/__main__.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtPrintSupport",
        "PySide6.QtWidgets",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="DartsLiga",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)
