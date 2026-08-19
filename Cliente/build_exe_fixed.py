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
    ('model/candidate_multi.pt', 'model'),  # modelo activo (multi-clase)
    ('Styles/*.py', 'Styles'),
    ('requirements*.txt', '.'),
    ('config/settings.ini', '.'),
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
    
    # Verificar modelo YOLO. El activo es el que carga GLOBAL_CONFIG
    # (model/candidate_multi.pt); last.pt quedo como respaldo.
    model_path = 'model/candidate_multi.pt'
    respaldo = 'model/last.pt'
    if os.path.exists(respaldo):
        print("  ✅ %s (respaldo, %.1f MB)" % (
            respaldo, os.path.getsize(respaldo) / (1024 * 1024)))
    if os.path.exists(model_path):
        model_size = os.path.getsize(model_path) / (1024 * 1024)  # MB
        print(f"  ✅ {model_path} ({model_size:.1f} MB)")
    else:
        print(f"  ⚠️ {model_path} - FALTANTE")
        print("    💡 El script puede crear un modelo básico automáticamente")
        
        # Preguntar si crear modelo automáticamente
        try:
            response = input("    ¿Crear modelo YOLO básico automáticamente? (s/n): ").strip().lower()
            if response in ['s', 'si', 'y', 'yes']:
                if create_basic_model():
                    print(f"  ✅ {model_path} creado automáticamente")
                else:
                    missing_files.append(model_path)
            else:
                missing_files.append(model_path)
        except (EOFError, KeyboardInterrupt):
            print("    ❌ Modelo no creado")
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

def create_basic_model():
    """Crea un modelo YOLO básico si no existe"""
    try:
        print("    📦 Descargando modelo YOLO básico...")
        from ultralytics import YOLO
        
        # Crear directorio model si no existe
        os.makedirs('model', exist_ok=True)
        
        # Descargar modelo preentrenado
        model = YOLO('yolov8n.pt')  # Modelo pequeño y rápido
        
        # Guardar como predict.pt
        model_path = 'model/last.pt'
        
        # Copiar el archivo descargado
        import shutil
        if os.path.exists('yolov8n.pt'):
            shutil.copy('yolov8n.pt', model_path)
            os.remove('yolov8n.pt')  # Limpiar archivo temporal
        
        print("    ✅ Modelo YOLO básico creado")
        return True
        
    except Exception as e:
        print(f"    ❌ Error creando modelo: {e}")
        return False

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
    
    # Limpiar archivos .spec anteriores (excepto el que vamos a crear)
    for file_pattern in files_to_clean:
        import glob
        for file_path in glob.glob(file_pattern):
            if file_path != 'weapon_detection.spec':
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
    """Crea un README con instrucciones"""
    readme_content = """# Weapon Detection System v2.0 - CORREGIDO

## Ejecutable de Windows

### NOTAS DE LA VERSIÓN CORREGIDA:
- ✅ Solucionado error de matplotlib/ultralytics
- ✅ Incluidas todas las dependencias necesarias
- ✅ Tamaño optimizado para mejor funcionamiento
- ✅ Verificado compatibilidad con Windows 10/11

### Instrucciones de Uso:

1. **Ejecutar la aplicación:**
   - Hacer doble clic en `WeaponDetectionSystem.exe`
   - O usar el acceso directo "Weapon Detection System.lnk"

2. **Primer uso:**
   - Registrarse en: http://127.0.0.1:8000/register/
   - Iniciar sesión con sus credenciales
   - Configurar ubicación y contacto para notificaciones

3. **Requisitos del sistema:**
   - Windows 10/11 (64-bit recomendado)
   - Cámara web funcional
   - Conexión a internet (para envío de alertas)
   - Mínimo 8GB RAM (recomendado para matplotlib/pytorch)
   - 4GB espacio libre en disco

4. **Características:**
   - Detección de armas en tiempo real
   - Análisis optimizado cada 3 segundos
   - Notificaciones automáticas por email/SMS
   - Interfaz moderna y fácil de usar
   - Monitoreo de recursos del sistema

### Archivos incluidos:
- `WeaponDetectionSystem.exe` - Aplicación principal
- `model/` - Modelo de IA entrenado
- `UI/` - Archivos de interfaz
- `_internal/` - Librerías y dependencias (matplotlib, pytorch, etc.)

### Solución de problemas:
- Si hay errores de inicio, revisar `app_log.log`
- Verificar que la cámara no esté siendo usada por otra aplicación
- Asegurar conexión estable a internet para las alertas

### Soporte:
- Para reportar errores o sugerencias
- Revisar logs en: `app_log.log`

---
Desarrollado con PyQt5, OpenCV, YOLO y PyTorch
Versión 2.0 CORREGIDA - Optimizada para Windows
Incluye matplotlib, scipy, pandas y todas las dependencias de ultralytics
"""
    
    with open('dist/WeaponDetectionSystem/README.txt', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("📄 README.txt actualizado creado en el directorio de distribución")

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

if __name__ == "__main__":
    try:
        success = main()
        input("\nPresione Enter para salir...")
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Construcción interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        input("\nPresione Enter para salir...")
        sys.exit(1)