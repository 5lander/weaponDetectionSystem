# -*- coding: utf-8 -*-
"""
Setup Build - Preparación automática para crear ejecutable
Weapon Detection System v2.0
"""

import os
import sys
import subprocess

def install_missing_packages():
    """Instala automáticamente los paquetes faltantes"""
    print("🔧 Instalando dependencias necesarias...")
    
    required_packages = [
        'pyinstaller>=6.0.0',
        'pillow>=8.0.0'
    ]
    
    for package in required_packages:
        print(f"📦 Instalando {package}...")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', package
            ])
            print(f"  ✅ {package} instalado")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Error instalando {package}: {e}")
            return False
    
    return True

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
        print(f"  ✅ {app_init} creado")
    
    # Crear __init__.py para Styles
    styles_init = 'Styles/__init__.py'
    if not os.path.exists(styles_init):
        os.makedirs('Styles', exist_ok=True)
        with open(styles_init, 'w', encoding='utf-8') as f:
            f.write('''# -*- coding: utf-8 -*-
"""Styles Package - Weapon Detection System v2.0"""
__version__ = "2.0.0"
''')
        print(f"  ✅ {styles_init} creado")
    
    return True

def create_model_if_missing():
    """Crea modelo YOLO si no existe"""
    model_path = 'model/last.pt'
    
    if not os.path.exists(model_path):
        print("🤖 Modelo YOLO no encontrado. Creando modelo básico...")
        
        try:
            from ultralytics import YOLO
            
            # Crear directorio
            os.makedirs('model', exist_ok=True)
            
            # Descargar modelo básico
            print("  📥 Descargando YOLOv8 nano...")
            model = YOLO('yolov8n.pt')
            
            # Copiar como predict.pt
            import shutil
            if os.path.exists('yolov8n.pt'):
                shutil.copy('yolov8n.pt', model_path)
                os.remove('yolov8n.pt')
                print(f"  ✅ Modelo creado: {model_path}")
                return True
            
        except Exception as e:
            print(f"  ❌ Error creando modelo: {e}")
            print("  💡 Puedes continuar sin modelo, pero la detección no funcionará")
            return False
    else:
        print(f"  ✅ Modelo encontrado: {model_path}")
        return True

def main():
    """Función principal de setup"""
    print("=" * 60)
    print("🚀 SETUP AUTOMÁTICO - WEAPON DETECTION SYSTEM v2.0")
    print("=" * 60)
    
    print("\n1️⃣ Instalando dependencias...")
    if not install_missing_packages():
        print("❌ Error en instalación de dependencias")
        return False
    
    print("\n2️⃣ Creando archivos necesarios...")
    if not create_missing_files():
        print("❌ Error creando archivos")
        return False
    
    print("\n3️⃣ Verificando/Creando modelo YOLO...")
    create_model_if_missing()  # No es crítico si falla
    
    print("\n" + "=" * 60)
    print("✅ SETUP COMPLETADO")
    print("=" * 60)
    print("🎯 Ahora puedes ejecutar: python build_exe.py")
    print("💡 O ejecutar directamente la aplicación: python main.py")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        input("\nPresione Enter para continuar...")
        if success:
            # Preguntar si ejecutar build automáticamente
            response = input("¿Ejecutar build_exe.py ahora? (s/n): ").strip().lower()
            if response in ['s', 'si', 'y', 'yes']:
                print("\n🔨 Ejecutando build_exe.py...")
                os.system('python build_exe.py')
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error en setup: {e}")
        input("\nPresione Enter para salir...")