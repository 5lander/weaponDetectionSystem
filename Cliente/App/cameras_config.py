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
    # candidate_multi.pt: modelo público multi-clase (6 clases: Grenade, Gun,
    # Knife, Pistol, handgun, rifle). Reemplazó a last.pt tras compararlos con
    # datos reales: detecta el cuchillo a 0.75-0.84 (vs 0.25-0.35 del viejo) y
    # las pistolas a 0.89-0.91 (vs 0.32-0.45). El viejo queda como respaldo.
    'model_path': 'model/candidate_multi.pt',
    
    # Servidor
    'server_url': 'https://weaponnotificationserver.onrender.com/api/images/',
    
    # Intervalos (segundos)
    'analysis_interval': 2,
    'capture_interval': 4,
    'resource_check_interval': 10,
    
    # Optimizaciones
    'use_gpu': True,
    'max_detections': 10,

    # ------------------------------------------------------------------
    # FILTROS ANTI-FALSOS-POSITIVOS (no requieren reentrenar el modelo)
    # ------------------------------------------------------------------
    # 1) Umbral de confianza: solo se aceptan detecciones por encima de esto.
    #    CALIBRADO para candidate_multi.pt con diagnóstico real en la webcam:
    #      - cuchillo real:        0.67-0.84 (cajas ajustadas)
    #      - falsos positivos:     <=0.43 (una caja confundida con arma de fuego)
    #    0.40 en VIVO: con movimiento/desenfoque el cuchillo baja de los 0.7-0.84
    #    que da posando quieto, así que 0.50 lo perdía casi siempre. 0.40 captura
    #    muchos más frames reales. El falso de la caja (~0.43) lo filtra ahora la
    #    confirmación temporal (2 de 4). Subir -> menos falsos; bajar -> más sensible.
    'confidence_threshold': 0.40,

    # 2) Confirmación temporal tipo "N de las últimas M": el arma debe verse en
    #    al menos N de los últimos M ciclos de análisis antes de alertar. Tolera
    #    el parpadeo de confianza (mejor que exigir frames perfectamente seguidos).
    #    Con analysis_interval=2s, "2 de 3" = el arma persiste ~4-6s. Mata los
    #    falsos de un solo frame sin perder armas reales que titilan.
    #    Poner confirmation_frames=1 = alerta inmediata (comportamiento anterior).
    'confirmation_frames': 2,   # N: detecciones requeridas
    'confirmation_window': 4,   # M: dentro de las últimas M ventanas de análisis
                                #    (2 de 4 ~= arma visible ~8s; alcanzable en vivo
                                #    aunque la detección titile, y filtra el falso aislado)

    # 3) Tamaño mínimo de caja (fracción del área del frame). OJO: candidate_multi.pt
    #    localiza MUY ajustado, así que un cuchillo real ocupa solo ~1.2-2.1% del
    #    encuadre. Por eso el filtro debe ser muy bajo (0.003 = 0.3%): solo mata
    #    motas de ruido de pocos píxeles, sin tocar las armas reales.
    #    (Con el modelo viejo esto era 0.02; subirlo aquí PERDERÍA detecciones.)
    'min_box_area_ratio': 0.003,

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


# ===========================================================================
# CARGA DE config/settings.ini
# ===========================================================================
# GLOBAL_CONFIG define los valores por defecto. settings.ini, si existe, los
# sobrescribe: asi se puede ajustar el comportamiento sin recompilar el .exe.
# Solo se aplican las claves declaradas en _INI_MAP; cualquier otra se ignora.
# Si el archivo falta o un valor esta mal escrito, se conserva el del codigo.

import configparser
import logging
import os
import sys

# (seccion del .ini, clave del .ini) -> (clave de GLOBAL_CONFIG, conversor)
_INI_MAP = {
    ('Detection', 'analysis_interval'):     ('analysis_interval', float),
    ('Detection', 'confidence_threshold'):  ('confidence_threshold', float),
    ('Detection', 'capture_interval'):      ('capture_interval', float),
    ('Detection', 'max_detections'):        ('max_detections', int),
    ('Detection', 'confirmation_frames'):   ('confirmation_frames', int),
    ('Detection', 'confirmation_window'):   ('confirmation_window', int),
    ('Detection', 'min_box_area_ratio'):    ('min_box_area_ratio', float),
    ('Detection', 'inference_workers'):     ('inference_workers', int),
    ('Camera', 'default_resolution_width'): ('display_width', int),
    ('Camera', 'default_resolution_height'):('display_height', int),
    ('Camera', 'cameras_per_row'):          ('cameras_per_row', int),
    ('Network', 'server_url'):              ('server_url', str),
    ('Network', 'max_reconnect_attempts'):  ('max_reconnect_attempts', int),
    ('Network', 'reconnect_delay'):         ('reconnect_delay', float),
}


def _app_dir():
    """Carpeta base de la aplicacion, tanto en desarrollo como empaquetada."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _settings_ini_path():
    return os.path.join(_app_dir(), 'config', 'settings.ini')


def load_settings_ini(config=None, path=None):
    """Sobrescribe `config` con lo que declare settings.ini.

    Devuelve un dict {clave: valor} con lo que se aplico, para poder registrarlo
    en el log. Nunca lanza: ante cualquier problema deja los valores por defecto.
    """
    config = GLOBAL_CONFIG if config is None else config
    path = _settings_ini_path() if path is None else path
    aplicados = {}

    if not os.path.isfile(path):
        logging.info("settings.ini no encontrado en %s; se usan los valores por "
                     "defecto de GLOBAL_CONFIG", path)
        return aplicados

    parser = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
    try:
        parser.read(path, encoding='utf-8')
    except (configparser.Error, OSError) as exc:
        logging.warning("No se pudo leer settings.ini (%s); se usan los valores "
                        "por defecto", exc)
        return aplicados

    for (seccion, clave), (destino, conversor) in _INI_MAP.items():
        if not parser.has_option(seccion, clave):
            continue
        crudo = parser.get(seccion, clave).strip()
        try:
            valor = conversor(crudo)
        except (TypeError, ValueError):
            logging.warning("settings.ini [%s] %s = %r no es valido; se conserva %r",
                            seccion, clave, crudo, config.get(destino))
            continue
        if config.get(destino) != valor:
            aplicados[destino] = valor
        config[destino] = valor

    if aplicados:
        logging.info("settings.ini aplicado: %s", aplicados)
    else:
        logging.info("settings.ini leido sin cambios respecto a los valores por defecto")
    return aplicados


# Se aplica al importar el modulo, antes de que nadie consulte GLOBAL_CONFIG.
load_settings_ini()
