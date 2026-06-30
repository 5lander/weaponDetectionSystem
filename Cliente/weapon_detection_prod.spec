# -*- mode: python ; coding: utf-8 -*-
# Weapon Detection System v2.0 - PyInstaller Spec (PRODUCCION / camaras Tapo RTSP)
#
# Diferencias clave frente a weapon_detection.spec original:
#   1) sys.setrecursionlimit(...) -> evita RecursionError de torch/ultralytics al analizar.
#   2) Se copian TODAS las DLLs de Intel MKL (+ libiomp5md) a la raiz del dist.
#      Sin esto, "import torch" crashea con 0xc06d007e (DLL no encontrada) porque
#      torch_cpu.dll depende de mkl_core/mkl_avx*/mkl_vml_* que PyInstaller no empaqueta.

import sys
import os
import glob

# (1) Fix RecursionError de torch/ultralytics durante el Analysis
sys.setrecursionlimit(sys.getrecursionlimit() * 5)

block_cipher = None
app_name = "WeaponDetectionSystem"

# Datos adicionales (van a la raiz del dist en modo onedir)
added_files = [
    ('UI/*.ui', 'UI'),
    ('model/last.pt', 'model'),
    ('Styles/*.py', 'Styles'),
    ('requirements*.txt', '.'),
    ('config/settings.ini', '.'),
]

# (2) CRITICO: recolectar el set completo de DLLs de Intel MKL + OpenMP
#     desde <Python>\Library\bin y copiarlas a la raiz del dist ('.').
_py_dir = os.path.dirname(sys.executable)
_mkl_dir = os.path.join(_py_dir, 'Library', 'bin')
mkl_binaries = []
if os.path.isdir(_mkl_dir):
    for _dll in glob.glob(os.path.join(_mkl_dir, 'mkl_*.dll')):
        mkl_binaries.append((_dll, '.'))
    for _extra in ('libiomp5md.dll', 'libiompstubs5md.dll'):
        _p = os.path.join(_mkl_dir, _extra)
        if os.path.exists(_p):
            mkl_binaries.append((_p, '.'))
print("[spec] MKL/OpenMP DLLs incluidas:", len(mkl_binaries), "desde", _mkl_dir)

# Icono opcional
icon_path = 'UI/icon.ico'
if not os.path.exists(icon_path):
    icon_path = None

hiddenimports = [
    # PyQt5
    'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'PyQt5.uic', 'PyQt5.sip',
    # Vision
    'cv2', 'numpy', 'PIL', 'PIL.Image',
    # YOLO / ultralytics
    'ultralytics', 'ultralytics.models', 'ultralytics.models.yolo',
    'ultralytics.models.yolo.detect', 'ultralytics.nn', 'ultralytics.nn.modules',
    'ultralytics.utils', 'ultralytics.data',
    # PyTorch
    'torch', 'torch.nn', 'torch.nn.functional', 'torchvision', 'torchvision.transforms',
    # Matplotlib (lo usa ultralytics)
    'matplotlib', 'matplotlib.pyplot', 'matplotlib.backends', 'matplotlib.backends.backend_agg',
    # Otras
    'requests', 'psutil', 'GPUtil', 'logging', 'threading', 'queue', 'time', 'json',
    'os', 'sys', 're', 'webbrowser', 'datetime', 'codecs', 'locale',
    'yaml', 'tqdm', 'scipy', 'pandas', 'seaborn',
]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=mkl_binaries,
    datas=added_files,
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
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,            # UPX puede corromper DLLs de MKL/torch -> mejor sin comprimir
    console=False,        # App con ventana (sin consola)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=app_name,
)
