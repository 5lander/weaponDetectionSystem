# -*- coding: utf-8 -*-
"""
Script CORREGIDO para crear ejecutable de Windows para Weapon Detection System v2.0
Solucionando el error de matplotlib y ultralytics
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# Los mensajes de progreso de este script llevan emojis. En Windows, cuando
# stdout NO es una consola UTF-8 (salida redirigida a un archivo, a una
# tuberia o lanzada desde otro script), el codec por defecto es cp1252 y el
# primer print() revienta con UnicodeEncodeError, abortando el build ANTES
# de empaquetar nada. Forzar UTF-8 en la salida lo evita.
for _flujo in (sys.stdout, sys.stderr):
    try:
        _flujo.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        pass

def create_spec_file():
    """Crea el archivo .spec personalizado CORREGIDO para PyInstaller"""
    
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-
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
'''
    
    with open('weapon_detection.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("✅ Archivo weapon_detection.spec corregido creado")

def check_dependencies():
    """Verifica que todas las dependencias estén instaladas - VERSIÓN CORREGIDA"""
    print("🔍 Verificando dependencias...")
    
    # Mapear nombres de paquetes pip a nombres de módulos - ACTUALIZADO
    package_modules = {
        'pyinstaller': 'PyInstaller',
        'PyQt5': 'PyQt5',
        'opencv-python': 'cv2',
        'ultralytics': 'ultralytics',
        'torch': 'torch',
        'torchvision': 'torchvision',
        'requests': 'requests',
        'psutil': 'psutil',
        'GPUtil': 'GPUtil',
        'pillow': 'PIL',
        'matplotlib': 'matplotlib',  # CRÍTICO - Ya no excluir
        'numpy': 'numpy',
        'pyyaml': 'yaml',
        'tqdm': 'tqdm',
        'scipy': 'scipy',
        'pandas': 'pandas',
        'seaborn': 'seaborn'
    }
    
    missing_packages = []
    
    for package_name, module_name in package_modules.items():
        try:
            __import__(module_name)
            print(f"  ✅ {package_name}")
        except ImportError:
            missing_packages.append(package_name)
            print(f"  ❌ {package_name} - FALTANTE")
    
    if missing_packages:
        print(f"\n⚠️ Instalar paquetes faltantes:")
        print(f"pip install {' '.join(missing_packages)}")
        
        # Ofrecer instalación automática
        try:
            response = input("\n¿Instalar automáticamente los paquetes faltantes? (s/n): ").strip().lower()
            if response in ['s', 'si', 'y', 'yes']:
                return install_missing_packages(missing_packages)
        except (EOFError, KeyboardInterrupt):
            pass
        
        return False
    
    print("✅ Todas las dependencias están instaladas")
    return True

def install_missing_packages(packages):
    """Instala paquetes faltantes automáticamente"""
    print("\n📦 Instalando paquetes faltantes...")
    
    for package in packages:
        print(f"  📥 Instalando {package}...")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', package, '--upgrade'
            ])
            print(f"  ✅ {package} instalado")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Error instalando {package}: {e}")
            return False
    
    print("✅ Todos los paquetes instalados correctamente")
    return True

def create_icon_if_missing():
    """Crea un icono básico si no existe"""
    icon_path = Path('UI/icon.ico')
    
    if not icon_path.exists():
        print("⚠️ No se encontró icon.ico, creando icono por defecto...")
        
        # Crear directorio UI si no existe
        icon_path.parent.mkdir(exist_ok=True)
        
        try:
            from PIL import Image, ImageDraw
            
            # Crear imagen de 256x256 con fondo azul
            img = Image.new('RGBA', (256, 256), (59, 130, 246, 255))
            draw = ImageDraw.Draw(img)
            
            # Dibujar un escudo simple
            shield_points = [
                (128, 40), (180, 70), (180, 150), (128, 200), (76, 150), (76, 70)
            ]
            draw.polygon(shield_points, fill=(255, 255, 255, 255))
            
            # Dibujar "WD" en el centro
            try:
                # Intentar usar fuente por defecto
                draw.text((105, 110), "WD", fill=(59, 130, 246, 255))
            except:
                # Si no hay fuente, dibujar formas simples
                draw.rectangle([100, 100, 110, 140], fill=(59, 130, 246, 255))
                draw.rectangle([120, 100, 130, 140], fill=(59, 130, 246, 255))
                draw.rectangle([140, 100, 150, 140], fill=(59, 130, 246, 255))
            
            # Guardar como ICO
            img.save(icon_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
            print(f"✅ Icono creado en {icon_path}")
            
        except ImportError:
            print("⚠️ PIL no disponible. Instalar con: pip install Pillow")
            # Crear archivo vacío para evitar errores
            icon_path.touch()
        except Exception as e:
            print(f"⚠️ Error creando icono: {e}")
            icon_path.touch()
    else:
        print(f"✅ Icono encontrado: {icon_path}")

def verify_project_structure():
    """Verifica que la estructura del proyecto sea correcta"""
    print("🔍 Verificando estructura del proyecto...")
    
    required_files = [
        'main.py',
        # Nombres actualizados tras el refactor del cliente
        # (antes: App/detection.py y App/detectionWindow.py).
        'App/detection_tapo.py',
        'App/detectionWindowDual.py',
        'App/inference_engine.py',
        'App/cameras_config.py',
        'App/loginWindowClass.py',
        'App/monitoringWindowClass.py',
        'UI/loginWindow.ui',
        'UI/monitoringWindow.ui',
        'UI/monitoringCameraWindow.ui',
        'Styles/loginStyle.py',
        'Styles/monitoringStyle.py',
        'config/settings.ini',
        'requirementsClient.txt'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"  ❌ {file_path} - FALTANTE")
    
    # Verificar modelo YOLO ACTIVO. Es el mismo que carga GLOBAL_CONFIG
    # (App/cameras_config.py -> 'model_path'). Si falta, el empaquetado se
    # aborta: NO se sustituye por un modelo generico, porque yolov8n detecta
    # personas y autos, no armas, y el .exe resultante pareceria funcionar
    # mientras no detecta nada.
    model_path = 'model/lastv2.pt'
    if os.path.exists(model_path):
        model_size = os.path.getsize(model_path) / (1024 * 1024)  # MB
        print(f"  ✅ {model_path} ({model_size:.1f} MB)")
    else:
        print(f"  ❌ {model_path} - FALTANTE (modelo de deteccion de armas)")
        missing_files.append(model_path)

    # Verificar archivos __init__.py
    init_files = ['App/__init__.py', 'Styles/__init__.py']
    for init_file in init_files:
        if not os.path.exists(init_file):
            print(f"  ⚠️ {init_file} - Creando...")
            create_init_file(init_file)
            print(f"  ✅ {init_file} - Creado")
    
    if missing_files:
        print(f"\n❌ Archivos faltantes críticos: {len(missing_files)}")
        return False
    
    print("✅ Estructura del proyecto correcta")
    return True

def create_init_file(file_path):
    """Crea archivos __init__.py básicos"""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        if 'App' in file_path:
            content = '''# -*- coding: utf-8 -*-
"""
App Package - Weapon Detection System v2.0
"""
__version__ = "2.0.0"
'''
        else:  # Styles
            content = '''# -*- coding: utf-8 -*-
"""
Styles Package - Weapon Detection System v2.0
"""
__version__ = "2.0.0"
'''
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    except Exception as e:
        print(f"    ❌ Error creando {file_path}: {e}")
        return False

def clean_previous_builds():
    """Limpia builds anteriores"""
    print("🧹 Limpiando builds anteriores...")
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    files_to_clean = ['*.spec']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"  🗑️ Eliminado: {dir_name}/")
    
    # Limpiar archivos .spec anteriores. Se conservan el que genera este script
    # y los versionados (*_prod.spec): esos son parte del repositorio.
    for file_pattern in files_to_clean:
        import glob
        for file_path in glob.glob(file_pattern):
            if file_path != 'weapon_detection.spec' and not file_path.endswith('_prod.spec'):
                os.remove(file_path)
                print(f"  🗑️ Eliminado: {file_path}")

def build_executable():
    """Construye el ejecutable usando PyInstaller"""
    print("\n🔨 Iniciando construcción del ejecutable...")
    print("⏳ Esto puede tomar varios minutos (especialmente con matplotlib incluido)...")
    
    try:
        # Ejecutar PyInstaller con el archivo spec
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',  # Limpiar cache
            '--noconfirm',  # No confirmar sobrescritura
            'weapon_detection.spec'
        ]
        
        print(f"Ejecutando: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print("✅ Ejecutable creado exitosamente!")
            print(f"📁 Ubicación: dist/WeaponDetectionSystem/")
            
            # Verificar que el ejecutable existe
            exe_path = "dist/WeaponDetectionSystem/WeaponDetectionSystem.exe"
            if os.path.exists(exe_path):
                exe_size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
                print(f"📊 Tamaño del ejecutable: {exe_size:.1f} MB")
                
                # Verificar tamaño total de la distribución
                total_size = sum(
                    os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, dirnames, filenames in os.walk("dist/WeaponDetectionSystem")
                    for filename in filenames
                ) / (1024 * 1024)
                print(f"📊 Tamaño total de distribución: {total_size:.1f} MB")
                
                # Crear acceso directo en el directorio actual
                create_shortcut()
                
                return True
            else:
                print("❌ El ejecutable no se encontró en la ubicación esperada")
                return False
        else:
            print("❌ Error durante la construcción:")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error ejecutando PyInstaller: {e}")
        return False

def create_shortcut():
    """Crea un acceso directo al ejecutable"""
    try:
        shortcut_path = "Weapon Detection System.lnk"
        exe_path = os.path.abspath("dist/WeaponDetectionSystem/WeaponDetectionSystem.exe")
        
        # Intentar crear acceso directo usando COM (Windows)
        if sys.platform == 'win32':
            try:
                import win32com.client
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(shortcut_path)
                shortcut.Targetpath = exe_path
                shortcut.WorkingDirectory = os.path.dirname(exe_path)
                shortcut.IconLocation = exe_path
                shortcut.save()
                print(f"🔗 Acceso directo creado: {shortcut_path}")
            except ImportError:
                print("⚠️ pywin32 no disponible para crear acceso directo")
        
    except Exception as e:
        print(f"⚠️ No se pudo crear acceso directo: {e}")

def create_readme():
    """Crea un README con instrucciones REALES para quien reciba el ejecutable.

    El README anterior estaba desactualizado en varios puntos que confunden a
    quien instala el sistema por primera vez: apuntaba a un servidor de
    desarrollo local (127.0.0.1:8000) en vez del servidor real, decia "cada 3
    segundos" cuando el intervalo efectivo es 2, y "4 GB de espacio" cuando el
    empaquetado con PyTorch+CUDA pesa mas de 5 GB.
    """
    from App.cameras_config import GLOBAL_CONFIG

    readme_content = """# Weapon Detection System - Guia de instalacion

## Como ejecutar (no requiere instalar nada)

1. Descomprimir esta carpeta completa en cualquier ubicacion (por ejemplo,
   el Escritorio). NO mover WeaponDetectionSystem.exe fuera de su carpeta:
   necesita los archivos que lo acompanan (model/, config/, UI/, etc.).
2. Hacer doble clic en WeaponDetectionSystem.exe.
3. En la ventana de login, usar las credenciales que se le hayan entregado,
   o pulsar "Registrarse" para crear una cuenta nueva.

## Primer arranque: qué es normal ver

- El servidor de alertas usa un plan gratuito que SE APAGA tras un rato sin
  uso. Si el login tarda hasta 30-40 segundos la primera vez, es normal: el
  servidor esta despertando. Los intentos siguientes tardan 1-3 segundos.
- El primer analisis de la camara tarda unos segundos mas que los siguientes
  (el motor de deteccion se prepara la primera vez). Despues de eso, cada
  analisis es casi instantaneo si el equipo tiene GPU NVIDIA, o de menos de
  un segundo si corre solo en CPU.
- La camara activa por defecto es la webcam del equipo (indice 0). Si el
  equipo no tiene camara integrada ni USB conectada, se debe conectar una
  antes de abrir la aplicacion.

## Como se decide que hay un arma

- Umbral de confianza: {umbral:.2f} (0.0 a 1.0). Mas alto = menos falsos
  positivos, pero puede perder detecciones borrosas o en movimiento.
- Confirmacion: el arma debe detectarse en {n} de los ultimos {m} analisis
  (cada uno cada {intervalo:.0f} s) antes de generar una alerta. Esto evita
  que un solo frame confuso dispare una alerta falsa.
- En la practica: sostener el objeto de prueba, quieto y visible frente a la
  camara, entre {espera_min:.0f} y {espera_max:.0f} segundos (lo justo para
  que entren 2 analisis dentro de esa ventana).
- Estos valores se ajustan en config/settings.ini sin necesidad de volver a
  generar el ejecutable (se leen cada vez que la aplicacion arranca).

## Requisitos del equipo

- Windows 10 o 11, 64-bit.
- Camara web (integrada o USB).
- Conexion a internet (para el login y el envio de alertas).
- Al menos {espacio} GB libres en disco.
- GPU NVIDIA: opcional. Si no hay, o sus drivers CUDA no coinciden, la
  aplicacion detecta esto sola y usa el procesador (CPU) sin fallar.

## Si algo no funciona

- Revisar el archivo app_log.log (se crea junto al .exe, en esta misma
  carpeta) despues de intentar usar la aplicacion: registra cada paso del
  arranque, la configuracion con la que corrio y cualquier error.
- Si aparece un error de conexion en el login: comprobar la conexion a
  internet y reintentar (puede ser el arranque en frio del servidor
  mencionado arriba).
- Si la camara no aparece o no abre: verificar que ninguna otra aplicacion
  (Zoom, Teams, etc.) la este usando en ese momento.

---
Sistema de Deteccion de Armas - Trabajo de tesis
PyQt5 + OpenCV + YOLO (Ultralytics) + PyTorch
"""
    espera_min = GLOBAL_CONFIG['confirmation_frames'] * GLOBAL_CONFIG['analysis_interval']
    espera_max = GLOBAL_CONFIG['confirmation_window'] * GLOBAL_CONFIG['analysis_interval']
    readme_content = readme_content.format(
        umbral=GLOBAL_CONFIG['confidence_threshold'],
        n=GLOBAL_CONFIG['confirmation_frames'],
        m=GLOBAL_CONFIG['confirmation_window'],
        intervalo=GLOBAL_CONFIG['analysis_interval'],
        espera_min=espera_min,
        espera_max=espera_max,
        espacio=6,
    )

    with open('dist/WeaponDetectionSystem/README.txt', 'w', encoding='utf-8') as f:
        f.write(readme_content)

def main():
    """Función principal del script de construcción CORREGIDO"""
    print("=" * 70)
    print("🔧 WEAPON DETECTION SYSTEM v2.0 - BUILDER CORREGIDO")
    print("🛠️ Solucionando error de matplotlib/ultralytics")
    print("=" * 70)
    
    # Verificar estructura del proyecto
    if not verify_project_structure():
        print("\n❌ Corrija los archivos faltantes antes de continuar")
        return False
    
    # Verificar dependencias
    if not check_dependencies():
        print("\n❌ Instale las dependencias faltantes antes de continuar")
        return False
    
    # Crear icono si no existe
    create_icon_if_missing()
    
    # Limpiar builds anteriores
    clean_previous_builds()
    
    # Crear archivo spec corregido
    create_spec_file()
    
    # Construir ejecutable
    if build_executable():
        create_readme()
        print("\n" + "=" * 70)
        print("🎉 ¡CONSTRUCCIÓN COMPLETADA EXITOSAMENTE!")
        print("🔧 ERROR DE MATPLOTLIB/ULTRALYTICS SOLUCIONADO")
        print("=" * 70)
        print("📁 Ejecutable disponible en: dist/WeaponDetectionSystem/")
        print("🚀 Para ejecutar: dist/WeaponDetectionSystem/WeaponDetectionSystem.exe")
        print("💡 Tip: El ejecutable ahora incluye todas las dependencias necesarias")
        print("📊 Nota: El tamaño será mayor debido a matplotlib/pytorch pero funcionará correctamente")
        return True
    else:
        print("\n" + "=" * 70)
        print("❌ CONSTRUCCIÓN FALLÓ")
        print("=" * 70)
        print("🔍 Revise los errores arriba y corrija antes de reintentar")
        return False

def _pausa():
    """Espera Enter SOLO si hay una terminal interactiva.

    Sin esto, al lanzar el build desde un script o CI (stdin cerrado) el
    input() lanza EOFError DESPUES de que el empaquetado ya termino bien, y
    ese error se reporta como si la construccion hubiera fallado.
    """
    try:
        if sys.stdin is not None and sys.stdin.isatty():
            input("\nPresione Enter para salir...")
    except (EOFError, KeyboardInterrupt, ValueError):
        pass


if __name__ == "__main__":
    try:
        success = main()
        _pausa()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Construcción interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        _pausa()
        sys.exit(1)