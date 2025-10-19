# -*- mode: python ; coding: utf-8 -*-
# Weapon Detection System v2.0 - PyInstaller Spec File CORREGIDO

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Configuración de paths
block_cipher = None
app_name = "WeaponDetectionSystem"

# Recopilar datos adicionales
added_files = [
    ('UI/*.ui', 'UI'),
    ('model/last.pt', 'model'),
    ('Styles/*.py', 'Styles'),
    ('requirements*.txt', '.'),
    ('config/settings.ini', '.'),
]

# Intentar agregar icono si existe
icon_path = 'UI/icon.ico'
if not os.path.exists(icon_path):
    icon_path = None

# Librerías ocultas necesarias - CORREGIDO PARA INCLUIR TODO LO NECESARIO
hiddenimports = [
    # PyQt5
    'PyQt5.QtCore',
    'PyQt5.QtGui', 
    'PyQt5.QtWidgets',
    'PyQt5.uic',
    'PyQt5.sip',
    
    # Computer Vision
    'cv2',
    'numpy',
    'PIL',
    'PIL.Image',
    
    # YOLO y dependencias - CRÍTICO
    'ultralytics',
    'ultralytics.models',
    'ultralytics.models.yolo',
    'ultralytics.models.yolo.detect',
    'ultralytics.nn',
    'ultralytics.nn.modules',
    'ultralytics.utils',
    'ultralytics.data',
    
    # PyTorch y dependencias
    'torch',
    'torch.nn',
    'torch.nn.functional',
    'torchvision',
    'torchvision.transforms',
    
    # Matplotlib - NECESARIO PARA ULTRALYTICS
    'matplotlib',
    'matplotlib.pyplot',
    'matplotlib.backends',
    'matplotlib.backends.backend_agg',
    
    # Otras dependencias críticas
    'requests',
    'psutil',
    'GPUtil',
    'logging',
    'threading',
    'queue',
    'time',
    'json',
    'os',
    'sys',
    're',
    'webbrowser',
    'datetime',
    'codecs',
    'locale',
    
    # Dependencias adicionales de ultralytics
    'yaml',
    'tqdm',
    'scipy',
    'pandas',
    'seaborn',  # Usado por ultralytics para visualización
]

# Análisis del archivo principal
a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=added_files,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],  # NO EXCLUIR NADA - Dejar que PyInstaller incluya todo lo necesario
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Filtrar archivos innecesarios para reducir tamaño (pero conservar lo esencial)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Crear ejecutable
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Comprimir ejecutable
    console=False,  # Sin ventana de consola
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,  # Icono de la aplicación
)

# Crear directorio de distribución
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=app_name,
)
