import PyInstaller.__main__
import os

# Obtén la ruta del directorio actual
current_dir = os.path.dirname(os.path.abspath(__file__))

PyInstaller.__main__.run([
    'main.py',
    '--onefile',
    '--windowed',
    f'--add-data={os.path.join(current_dir, "UI")}:UI',
    f'--add-data={os.path.join(current_dir, "model")}:model',
    f'--add-data={os.path.join(current_dir, "savedFrame")}:savedFrame',
    '--collect-all=ultralytics',
    '--name=WeaponDetectionApp'
])