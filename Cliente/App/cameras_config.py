# -*- coding: utf-8 -*-
"""
cameras_config.py - Configuración de cámaras Tapo C310
Define aquí todas tus cámaras para fácil gestión
"""

# ========================================
# CONFIGURACIÓN DE TUS 2 CÁMARAS
# ========================================

CAMERAS_CONFIG = {
    'camera_1': {
        'name': 'Cámara Principal',
        'ip': '192.168.1.10',
        'username': 'Lander',
        'password': 'lander123',
        'stream': 'stream1',  # Alta calidad: 2304x1296
        'port': 554,
        'location': 'Entrada Principal',
        'enabled': True
    },
    'camera_2': {
        'name': 'Cámara Secundaria',
        'ip': '192.168.1.20',  # CAMBIA ESTA IP POR LA DE TU SEGUNDA CÁMARA
        'username': 'Lander1',
        'password': 'lander123',
        'stream': 'stream1',  # Alta calidad
        'port': 554,
        'location': 'Área de Trabajo',
        'enabled': True
    }
}

# ========================================
# CONFIGURACIÓN GLOBAL
# ========================================

GLOBAL_CONFIG = {
    # Modelo YOLO
    'model_path': 'model/last.pt',
    
    # Servidor
    'server_url': 'http://tu-servidor.com/api/upload',
    
    # Intervalos (segundos)
    'analysis_interval': 2,      # Analizar cada 2 segundos
    'capture_interval': 4,       # Guardar detecciones cada 4 segundos
    'resource_check_interval': 10,  # Verificar recursos cada 10 segundos
    
    # Optimizaciones
    'use_gpu': True,             # Usar GPU si está disponible
    'max_detections': 10,        # Máximo de detecciones por frame
    'confidence_threshold': 0.5, # Confianza mínima
    
    # Recuperación de errores
    'max_reconnect_attempts': 3,
    'reconnect_delay': 2,
    
    # UI
    'display_width': 640,
    'display_height': 480
}

# ========================================
# FUNCIONES DE UTILIDAD
# ========================================

def get_enabled_cameras():
    """Retorna lista de cámaras habilitadas"""
    return {
        key: config 
        for key, config in CAMERAS_CONFIG.items() 
        if config.get('enabled', True)
    }

def get_camera_config(camera_key):
    """Obtener configuración de una cámara específica"""
    return CAMERAS_CONFIG.get(camera_key)

def validate_camera_config(config):
    """Validar que la configuración de cámara esté completa"""
    required_fields = ['ip', 'username', 'password', 'location']
    for field in required_fields:
        if not config.get(field):
            return False, f"Campo requerido faltante: {field}"
    return True, "OK"

# ========================================
# TIPS DE CONFIGURACIÓN
# ========================================

"""
CONFIGURACIÓN DE CALIDAD:

1. Para ALTA CALIDAD (detección precisa):
   'stream': 'stream1'
   Resolución: 2304x1296 @ 15fps
   Ancho de banda: ~4-6 Mbps por cámara
   
2. Para BAJA CALIDAD (ahorro de ancho de banda):
   'stream': 'stream2'
   Resolución: 640x360 @ 15fps
   Ancho de banda: ~1-2 Mbps por cámara

RECOMENDACIÓN PARA 2 CÁMARAS:
- Si tu red soporta 10+ Mbps: Usa stream1 en ambas
- Si tu red es limitada: stream1 en principal, stream2 en secundaria

CÓMO ENCONTRAR LA IP DE TU SEGUNDA CÁMARA:
1. Abre app Tapo
2. Selecciona la segunda cámara
3. Toca engranaje ⚙️ → Device Info
4. Anota la IP y cámbiala arriba en camera_2

IMPORTANTE:
- Asegúrate que ambas cámaras tengan Camera Account creada
- Usa las mismas credenciales para facilitar gestión
- Si usas diferentes usuarios/passwords, cámbialos arriba
"""