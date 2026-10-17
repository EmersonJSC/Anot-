# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import sys
import os

block_cipher = None

datas = []
datas += collect_data_files('customtkinter')
datas += collect_data_files('tkinterdnd2')
datas += collect_data_files('faster_whisper')

hiddenimports = []
hiddenimports += collect_submodules('customtkinter')
hiddenimports += collect_submodules('tkinterdnd2')
hiddenimports += collect_submodules('faster_whisper')
hiddenimports += collect_submodules('ctranslate2')
hiddenimports += ['src', 'src.ui', 'src.transcriber', 'src.audio_processor', 'src.exporter', 'src.model_manager', 'src.storage']

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    [],
    exclude_binaries=True,
    name='TranscritorLocal',
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
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TranscritorLocal',
)
