# -*- coding: utf-8 -*-
"""
Styles Package - Weapon Detection System v2.0
Contiene todos los estilos CSS/QSS para las ventanas
"""

__version__ = "2.0.0"
__description__ = "Estilos y temas para la interfaz de usuario"

# Importaciones de estilos
from .loginStyle import LoginWindowStyles, StatusIndicatorStyles
from .monitoringStyle import MonitoringWindowStyles, MonitoringStatusIndicatorStyles
from .detectionWindowStyle import DetectionWindowStyles, DetectionStatusStyles, ResourceIndicatorStyles

__all__ = [
    'LoginWindowStyles',
    'StatusIndicatorStyles',
    'MonitoringWindowStyles', 
    'MonitoringStatusIndicatorStyles',
    'DetectionWindowStyles',
    'DetectionStatusStyles',
    'ResourceIndicatorStyles'
]