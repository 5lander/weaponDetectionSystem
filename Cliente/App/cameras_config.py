# -*- coding: utf-8 -*-
"""
cameras_config.py - SISTEMA DINÁMICO ESCALABLE
Agrega todas las cámaras que necesites
"""



# ========================================
# CONFIGURACIÓN GLOBAL
# ========================================

GLOBAL_CONFIG = {
    # Modelo YOLO
    'model_path': 'model/last.pt',
    
    # Servidor
    'server_url': 'https://weaponnotificationserver.onrender.com/api/images/',
    
    # Intervalos (segundos)
    'analysis_interval': 2,
    'capture_interval': 4,
    'resource_check_interval': 10,
    
    # Optimizaciones
    'use_gpu': True,
    'max_detections': 10,
    'confidence_threshold': 0.5,

    # Motor de inferencia compartido: nº de workers de inferencia (1 modelo en RAM
    # para todas las cámaras). Default 1; subir a 2 solo si la GPU lo permite.
    'inference_workers': 1,
    
    # Recuperación de errores
    'max_reconnect_attempts': 3,
    'reconnect_delay': 2,
    
    # UI - Configuración de pantalla
    'cameras_per_row': 2,  # Cuántas cámaras mostrar por fila
    'display_width': 640,
    'display_height': 480
}

