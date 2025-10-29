# -*- coding: utf-8 -*-
"""
App Package - Weapon Detection System v2.0
Contiene todas las clases principales de la aplicación
"""

__version__ = "2.0.0"
__author__ = "Weapon Detection Team"
__description__ = "Sistema de Detección de Armas con IA"

# Importaciones principales del paquete
from .detection import Detection
from .detection_tapo import DetectionTapo
from .detectionWindowDual import DetectionWindowDual
from .loginWindowClass import LoginWindow
from .monitoringWindowClass import MonitoringWindow
from .detectionWindow import DetectionWindow
from .cameraManagerWindow import CameraManagerWindow 

__all__ = [
    'Detection',
    'DetectionTapo',
    'DetectionWindowDual',
    'LoginWindow', 
    'MonitoringWindow',
    'DetectionWindow',
    'CameraManagerWindow'  # AGREGAR AQUÍ
]