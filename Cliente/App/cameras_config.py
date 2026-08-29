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
    # lastv2.pt: modelo multi-clase ACTIVO (6 clases: Grenade, Gun, Knife,
    # Pistol, handgun, rifle). Reemplazó al modelo de 2 clases tras compararlos
    # con datos reales: detecta el cuchillo a 0.75-0.84 (vs 0.25-0.35 del viejo)
    # y las pistolas a 0.89-0.91 (vs 0.32-0.45).
    'model_path': 'model/lastv2.pt',
    
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
    #
    #    OJO: este 0.40 es solo el DEFAULT del código. config/settings.ini
    #    declara confidence_threshold=0.60 y SOBRESCRIBE este valor al arrancar
    #    (ver load_settings_ini abajo), así que el umbral EFECTIVO es 0.60.
    #    Para cambiarlo de verdad hay que editar settings.ini, no esta línea.
    #
    #    Medido con lastv2.pt en diagnóstico real:
    #      - arma real, posando quieta:  0.67-0.91
    #      - arma real, en movimiento:   baja de 0.70 (desenfoque)
    #      - falso positivo típico:      <=0.43 (una caja rectangular)
    #
    #    Compromiso elegido con 0.60: pensado para demostración en vivo. Con
    #    0.70 se perdía el arma en movimiento (y con la confirmación 2 de 4
    #    hacen falta ~8 s de detección sostenida para alertar). 0.60 recupera
    #    los frames con desenfoque sin acercarse al ~0.43 del falso positivo
    #    típico, que además la confirmación temporal filtra por sí sola.
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

    # 3) VENTANA DE TAMAÑO DE CAJA (fracción del área del frame).
    #    Estos dos valores son los DEFAULTS GLOBALES, pensados para el escenario
    #    de primer plano (webcam de pruebas). Cada cámara puede sobrescribirlos
    #    con su propio escenario: ver SCENE_PROFILES más abajo.
    #
    #    Mínimo: lastv2.pt localiza MUY ajustado, así que un cuchillo a
    #    1 m ocupa solo ~1.2-2.1% del encuadre. 0.003 (0.3%) mata las motas de
    #    ruido de pocos píxeles sin tocar las armas reales de ese escenario.
    'min_box_area_ratio': 0.003,

    #    Máximo: descarta las cajas ABSURDAMENTE GRANDES para ser un arma.
    #    Medido con falsos positivos reales de una cámara de calle: el modelo
    #    clasificaba AUTOS enteros como 'Knife' con confianza 0.86 y 'Pistol'
    #    con 0.80, con cajas de 8%-38% del encuadre. Subir el umbral de confianza
    #    NO los filtra (superan a las armas reales, que dan 0.63-0.79); lo que
    #    sí los separa es el tamaño. 0.60 es un tope global muy permisivo, que
    #    solo mata lo absurdo y no toca el primer plano; las cámaras de
    #    vigilancia deben usar su escenario (0.10 interior, 0.02 exterior).
    'max_box_area_ratio': 0.60,

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
# PERFILES DE ESCENARIO (ventana de tamaño de caja por cámara)
# ===========================================================================
# El tamaño que ocupa un arma en el encuadre depende de la GEOMETRÍA de cada
# cámara, no del modelo. Por eso los límites de tamaño no pueden ser globales:
#
#   - Webcam a 1 m:        un cuchillo ocupa 3%-25% del encuadre.
#   - Cámara de calle a 12 m: un arma ocuparía ~0.03% (unos 30x15 px),
#                          mientras que un AUTO ocupa 8%-14%.
#
# Con un único par de límites, o se filtran las armas reales de la calle, o se
# dejan pasar los autos. Cada cámara declara su escenario en cameras.json con
# la clave "scene"; si no la declara, se usan los valores globales.
#
#   clave -> (etiqueta para la interfaz, min_box_area_ratio, max_box_area_ratio)

SCENE_PROFILES = {
    'closeup': (
        'Primer plano / pruebas con webcam (menos de 2 m)',
        0.003, 0.60,
    ),
    'indoor': (
        'Interior: entrada, pasillo, sala (3 a 6 m)',
        0.001, 0.10,
    ),
    'outdoor': (
        'Exterior: calle, patio, estacionamiento (más de 10 m)',
        0.0002, 0.02,
    ),
    'custom': (
        'Personalizado (valores del archivo de configuración)',
        None, None,
    ),
}

DEFAULT_SCENE = 'closeup'


def scene_label(scene):
    """Etiqueta legible de un escenario."""
    perfil = SCENE_PROFILES.get((scene or '').lower())
    return perfil[0] if perfil else SCENE_PROFILES[DEFAULT_SCENE][0]


def box_area_limits(camera_config=None, config=None):
    """Ventana de tamaño de caja (min, max) efectiva para una cámara.

    Prioridad, de mayor a menor:
      1. min_box_area_ratio / max_box_area_ratio explícitos en la cámara.
      2. El perfil del escenario declarado en la cámara ("scene").
      3. Los valores globales de GLOBAL_CONFIG (ajustables por settings.ini).

    Nunca lanza: ante cualquier dato inválido cae al nivel siguiente.
    """
    config = GLOBAL_CONFIG if config is None else config
    camera_config = camera_config or {}

    minimo = config.get('min_box_area_ratio', 0.0)
    maximo = config.get('max_box_area_ratio', 1.0)

    perfil = SCENE_PROFILES.get(str(camera_config.get('scene', '') or '').lower())
    if perfil and perfil[1] is not None:
        minimo, maximo = perfil[1], perfil[2]

    for clave, actual in (('min_box_area_ratio', 'min'), ('max_box_area_ratio', 'max')):
        if clave in camera_config:
            try:
                valor = float(camera_config[clave])
            except (TypeError, ValueError):
                logging.warning("Cámara con %s = %r no numérico; se ignora",
                                clave, camera_config[clave])
                continue
            if actual == 'min':
                minimo = valor
            else:
                maximo = valor

    # Saneado: el mínimo nunca por debajo de 0 ni por encima del máximo.
    minimo = max(0.0, float(minimo))
    maximo = float(maximo)
    if maximo <= 0:
        maximo = 1.0
    if minimo >= maximo:
        logging.warning("Límites de tamaño incoherentes (min=%s >= max=%s); "
                        "se ignora el mínimo", minimo, maximo)
        minimo = 0.0
    return minimo, maximo


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
    ('Detection', 'max_box_area_ratio'):    ('max_box_area_ratio', float),
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


def camera_key_number(key, por_defecto=0):
    """Numero de una clave tipo 'camera_N'. NUNCA lanza.

    Las claves de cameras.json las escribe tanto la aplicacion (camera_1,
    camera_2...) como una persona editandolo a mano, y ahi puede aparecer
    cualquier sufijo (p.ej. 'camera_webcam'). El gestor de camaras hacia int()
    directo sobre ese sufijo, asi que una sola clave no numerica impedia ABRIR
    la ventana entera con "invalid literal for int()".
    """
    try:
        return int(str(key).rsplit('_', 1)[1])
    except (IndexError, ValueError, TypeError):
        return por_defecto


def cameras_json_path():
    """Ruta de cameras.json JUNTO A LA APLICACION (no al directorio de trabajo).

    Antes se abria como 'cameras.json' a secas, es decir relativo al cwd. En el
    ejecutable eso significa que, si se lanza desde otra carpeta (un acceso
    directo con "Iniciar en" distinto, o un doble clic desde otra ruta), la app
    NO encuentra la configuracion real y se crea una por defecto con una camara
    de ejemplo (192.168.1.10 / admin / password) que nunca conecta.
    """
    return os.path.join(_app_dir(), 'cameras.json')


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
