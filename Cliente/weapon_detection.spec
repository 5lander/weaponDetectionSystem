# -*- mode: python ; coding: utf-8 -*-
# Weapon Detection System v2.0 - PyInstaller Spec File CORREGIDO

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# torch/ultralytics importan módulos muy anidados y PyInstaller topa con el
# límite de recursión de Python (RecursionError). Subirlo es el fix oficial.
sys.setrecursionlimit(5000)

# Configuración de paths
block_cipher = None
app_name = "WeaponDetectionSystem"

# Recopilar datos adicionales
added_files = [
    ('UI/*.ui', 'UI'),
    # El icono NO estaba: el .spec solo copiaba *.ui, asi que la app lo
    # buscaba en runtime (resource_path('UI/icon.ico')) y no lo encontraba;
    # las ventanas salian con el icono generico de Windows. El parametro
    # icon= de EXE solo cubre el icono del archivo .exe, no el de las ventanas.
    ('UI/icon.ico', 'UI'),
    ('model/lastv2.pt', 'model'),  # modelo activo (multi-clase)
    ('Styles/*.py', 'Styles'),
    ('requirements*.txt', '.'),
    # settings.ini DEBE quedar en dist/config/, que es donde lo busca
    # cameras_config._settings_ini_path() (<dir de la app>/config/settings.ini).
    # Con destino '.' caia en la raiz del dist y la app NUNCA lo leia: el
    # ejecutable corria con los valores por defecto del codigo, ignorando
    # el umbral, los intervalos y la URL del servidor configurados.
    ('config/settings.ini', 'config'),
    # cameras.json va JUNTO AL EXE (la app lo lee y lo reescribe desde el
    # gestor de camaras). Sin esto, al arrancar no encuentra ninguna camara
    # configurada y se crea una de ejemplo que nunca conecta.
    ('cameras.json', '.'),
]

# --- Intel MKL (CRITICO): torch delay-carga en runtime mkl_core/mkl_def/
# mkl_avx2/etc. PyInstaller NO las detecta (carga dinamica), y sin ellas el
# .exe crashea al importar torch con 0xC06D007E (module not found), justo tras
# cargar torch _C.pyd. Se copian todas desde <prefix>/Library/bin al bundle.
import glob as _glob
_mkl_bin = os.path.join(sys.prefix, 'Library', 'bin')
for _pat in ('mkl_*.dll', 'libiomp*.dll'):
    for _dll in _glob.glob(os.path.join(_mkl_bin, _pat)):
        added_files.append((_dll, '.'))

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
# ---------------------------------------------------------------------------
# PESO MUERTO DE TORCH: el wheel de PyTorch trae, junto a las DLL, sus
# bibliotecas ESTATICAS de enlace (*.lib, ~744 MB, de los cuales dnnl.lib solo
# ya son 606 MB) y las cabeceras C++ de torch/include (~50 MB, 8400 archivos).
# Sirven para COMPILAR extensiones C++ contra libtorch, no para ejecutar:
# todos los .lib empiezan por "!<arch>" (archivo estatico COFF), y Windows
# solo puede cargar DLLs en runtime. oneDNN, por ejemplo, va enlazado dentro
# de torch_cpu.dll; no existe ningun dnnl.dll que cargar.
# Verificado: quitandolos, el ejecutable arranca igual.
def _sin_peso_muerto(lista):
    limpia = []
    for entrada in lista:
        destino = entrada[0].replace(chr(92), "/").lower()
        if destino.endswith(".lib"):
            continue
        if destino.startswith("torch/include/"):
            continue
        limpia.append(entrada)
    return limpia


a.binaries = _sin_peso_muerto(a.binaries)
a.datas = _sin_peso_muerto(a.datas)
# ---------------------------------------------------------------------------

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
