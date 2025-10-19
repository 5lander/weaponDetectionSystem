# -*- coding: utf-8 -*-
"""
Setup Build CORREGIDO - Preparación automática para crear ejecutable
Weapon Detection System v2.0 - Solucionando error de matplotlib
"""

import os
import sys
import subprocess

def install_missing_packages():
    """Instala automáticamente los paquetes faltantes - VERSIÓN CORREGIDA"""
    print("🔧 Instalando dependencias necesarias (incluyendo matplotlib)...")
    
    required_packages = [
        'pyinstaller>=6.0.0',
        'pillow>=8.0.0',
        'matplotlib>=3.5.0',  # CRÍTICO - Necesario para ultralytics
        'scipy>=1.7.0',       # Dependencia de matplotlib
        'pandas>=1.3.0',      # Usado por ultralytics
        'seaborn>=0.11.0',    # Usado por ultralytics para visualización
        'pyyaml>=5.4.0',      # Necesario para configuraciones de YOLO
        'tqdm>=4.60.0',       # Barras de progreso
        'opencv-python>=4.5.0',
        'ultralytics>=8.0.0',
        'torch>=1.9.0',
        'torchvision>=0.10.0',
        'numpy>=1.21.0',
        'requests>=2.25.0',
        'psutil>=5.8.0',
        'GPUtil>=1.4.0',
        'PyQt5>=5.15.0'
    ]
    
    for package in required_packages:
        print(f"📦 Instalando {package}...")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', package, '--upgrade'
            ])
            print(f"  ✅ {package} instalado")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Error instalando {package}: {e}")
            print(f"  🔄 Intentando instalación alternativa...")
            
            # Intentar instalación sin upgrade
            try:
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install', package
                ])
                print(f"  ✅ {package} instalado (modo alternativo)")
            except subprocess.CalledProcessError as e2:
                print(f"  ❌ Error en instalación alternativa: {e2}")
                return False
    
    return True

def verify_critical_imports():
    """Verifica que las importaciones críticas funcionen"""
    print("🔍 Verificando importaciones críticas...")
    
    critical_modules = [
        ('PyQt5', 'PyQt5.QtWidgets'),
        ('OpenCV', 'cv2'),
        ('NumPy', 'numpy'),
        ('Matplotlib', 'matplotlib.pyplot'),
        ('Ultralytics', 'ultralytics'),
        ('PyTorch', 'torch'),
        ('PIL', 'PIL'),
        ('Requests', 'requests'),
        ('PSUtil', 'psutil'),
        ('GPUtil', 'GPUtil'),
        ('YAML', 'yaml'),
        ('TQDM', 'tqdm'),
        ('Scipy', 'scipy'),
        ('Pandas', 'pandas'),
        ('Seaborn', 'seaborn')
    ]
    
    failed_imports = []
    
    for name, module in critical_modules:
        try:
            __import__(module)
            print(f"  ✅ {name}")
        except ImportError as e:
            print(f"  ❌ {name} - Error: {e}")
            failed_imports.append((name, module))
    
    if failed_imports:
        print(f"\n⚠️ Módulos fallidos: {len(failed_imports)}")
        for name, module in failed_imports:
            print(f"  - {name} ({module})")
        return False
    
    print("✅ Todas las importaciones críticas funcionan correctamente")
    return True

def test_ultralytics_functionality():
    """Prueba específica para ultralytics y matplotlib"""
    print("🧪 Probando funcionalidad de Ultralytics + Matplotlib...")
    
    try:
        # Probar importación completa de ultralytics
        from ultralytics import YOLO
        print("  ✅ YOLO importado correctamente")
        
        # Probar matplotlib (que causa el error)
        import matplotlib.pyplot as plt
        print("  ✅ Matplotlib importado correctamente")
        
        # Probar que ultralytics puede usar matplotlib
        import ultralytics.utils
        print("  ✅ Ultralytics utils (con matplotlib) funciona")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Error en test de ultralytics: {e}")
        return False
    except Exception as e:
        print(f"  ⚠️ Advertencia en test de ultralytics: {e}")
        return True  # Continuar aunque haya advertencias

def create_missing_files():
    """Crea archivos faltantes necesarios"""
    print("📁 Creando archivos necesarios...")
    
    # Crear __init__.py para App
    app_init = 'App/__init__.py'
    if not os.path.exists(app_init):
        os.makedirs('App', exist_ok=True)
        with open(app_init, 'w', encoding='utf-8') as f:
            f.write('''# -*- coding: utf-8 -*-
"""App Package - Weapon Detection System v2.0"""
__version__ = "2.0.0"
''')