# -*- coding: utf-8 -*-
"""
cameras_config.py - SISTEMA DINÁMICO ESCALABLE
Agrega todas las cámaras que necesites
"""

# ========================================
# CONFIGURACIÓN DE CÁMARAS - ¡AGREGA LAS QUE NECESITES!
# ========================================

CAMERAS_CONFIG = {
    # Puedes agregar tantas cámaras como necesites
    # Solo cambia el número: 'camera_1', 'camera_2', 'camera_3', etc.
    
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
        'ip': '192.168.1.20',
        'username': 'Lander1',
        'password': 'lander123',
        'stream': 'stream1',
        'port': 554,
        'location': 'Área de Trabajo',
        'enabled': True
    },

        'camera_3': {
        'name': 'Cámara Secundaria',
        'ip': '192.168.1.21',
        'username': 'Lander1',
        'password': 'lander123',
        'stream': 'stream1',
        'port': 554,
        'location': 'Área de Trabajo',
        'enabled': True
    },
    # EJEMPLO: Agrega más cámaras copiando este formato
    # 'camera_3': {
    #     'name': 'Cámara Estacionamiento',
    #     'ip': '192.168.1.30',
    #     'username': 'admin',
    #     'password': 'password123',
    #     'stream': 'stream1',
    #     'port': 554,
    #     'location': 'Estacionamiento',
    #     'enabled': True
    # },
    # 'camera_4': {
    #     'name': 'Cámara Almacén',
    #     'ip': '192.168.1.40',
    #     'username': 'admin',
    #     'password': 'password123',
    #     'stream': 'stream1',
    #     'port': 554,
    #     'location': 'Almacén',
    #     'enabled': True
    # },
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
    'analysis_interval': 2,
    'capture_interval': 4,
    'resource_check_interval': 10,
    
    # Optimizaciones
    'use_gpu': True,
    'max_detections': 10,
    'confidence_threshold': 0.5,
    
    # Recuperación de errores
    'max_reconnect_attempts': 3,
    'reconnect_delay': 2,
    
    # UI - Configuración de pantalla
    'cameras_per_row': 2,  # Cuántas cámaras mostrar por fila
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

def get_total_cameras():
    """Obtener número total de cámaras configuradas"""
    return len(CAMERAS_CONFIG)

def get_camera_number(camera_key):
    """Extraer número de cámara desde la key (ej: 'camera_1' -> 1)"""
    try:
        return int(camera_key.split('_')[1])
    except:
        return 0

def validate_camera_config(config):
    """Validar que la configuración de cámara esté completa"""
    required_fields = ['ip', 'username', 'password', 'location']
    for field in required_fields:
        if not config.get(field):
            return False, f"Campo requerido faltante: {field}"
    return True, "OK"

def add_camera_to_config(camera_num, name, ip, username, password, location, stream='stream1'):
    """
    Agregar una nueva cámara al diccionario (útil para GUI dinámica)
    
    Args:
        camera_num: Número de cámara
        name: Nombre descriptivo
        ip: Dirección IP
        username: Usuario RTSP
        password: Contraseña RTSP
        location: Ubicación física
        stream: 'stream1' o 'stream2'
    """
    key = f'camera_{camera_num}'
    CAMERAS_CONFIG[key] = {
        'name': name,
        'ip': ip,
        'username': username,
        'password': password,
        'stream': stream,
        'port': 554,
        'location': location,
        'enabled': True
    }
    return key

def remove_camera_from_config(camera_key):
    """Remover una cámara del diccionario"""
    if camera_key in CAMERAS_CONFIG:
        del CAMERAS_CONFIG[camera_key]
        return True
    return False

# ========================================
# TIPS DE CONFIGURACIÓN
# ========================================

"""
🎥 CÓMO AGREGAR MÁS CÁMARAS:

1. MÉTODO MANUAL (Editar este archivo):
   - Copia el bloque de cualquier cámara existente
   - Cambia el número: 'camera_3', 'camera_4', etc.
   - Actualiza los datos (IP, usuario, ubicación)

2. MÉTODO DINÁMICO (Desde la interfaz):
   - La GUI ahora detecta automáticamente todas las cámaras
   - Solo necesitas agregar el bloque aquí arriba

EJEMPLO PARA 5 CÁMARAS:
-------------------------
CAMERAS_CONFIG = {
    'camera_1': {...},  # Entrada
    'camera_2': {...},  # Oficina
    'camera_3': {...},  # Estacionamiento
    'camera_4': {...},  # Almacén
    'camera_5': {...},  # Salida
}

RECOMENDACIONES POR NÚMERO DE CÁMARAS:
- 1-2 cámaras: stream1 (alta calidad) en todas
- 3-4 cámaras: stream1 en principales, stream2 en secundarias
- 5+ cámaras: Mezclar stream1 y stream2 según importancia

DISTRIBUCIÓN EN PANTALLA:
- 1-2 cámaras: Una al lado de la otra
- 3-4 cámaras: Grid 2x2
- 5-6 cámaras: Grid 2x3
- 7-9 cámaras: Grid 3x3
- 10+ cámaras: Scroll vertical automático

ANCHO DE BANDA ESTIMADO (por cámara):
- stream1: ~4-6 Mbps
- stream2: ~1-2 Mbps

Para 5 cámaras en stream1: ~25-30 Mbps total
Para 5 cámaras en stream2: ~5-10 Mbps total
"""