# -*- coding: utf-8 -*-
"""
App Package - Weapon Detection System v2.0
Contiene todas las clases principales de la aplicación
"""

__version__ = "2.0.0"
__author__ = "Weapon Detection Team"
__description__ = "Sistema de Detección de Armas con IA"

# Importaciones principales del paquete
from .detection_tapo import DetectionTapo
from .detectionWindowDual import DetectionWindowDual
from .loginWindowClass import LoginWindow
from .monitoringWindowClass import MonitoringWindow
from .cameraManagerWindow import CameraManagerWindow
from .inference_engine import InferenceEngine

__all__ = [
    'DetectionTapo',
    'DetectionWindowDual',
    'LoginWindow',
    'MonitoringWindow',
    'CameraManagerWindow',
    'InferenceEngine'
]