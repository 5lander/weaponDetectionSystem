# -*- coding: utf-8 -*-
"""
rtsp_profiles.py - Perfiles RTSP por marca de cámara (fuente única de verdad).

Permite que el sistema funcione con CUALQUIER cámara:
- Marcas con plantilla automática: Tapo, Hikvision, Dahua, Reolink.
- "Genérica / Otra": el usuario escribe la ruta RTSP a mano (o pega la URL completa).

Todo el resto del código (formularios y detección) debe usar build_rtsp_url()
para no repetir el formato en varios lugares.
"""

from urllib.parse import quote

# (clave, etiqueta para mostrar). El orden es el que se ve en el combo.
BRANDS = [
    ('tapo', 'Tapo (TP-Link)'),
    ('hikvision', 'Hikvision'),
    ('dahua', 'Dahua'),
    ('reolink', 'Reolink'),
    ('custom', 'Genérica / Otra (ruta manual)'),
]

# Calidad de stream: clave canónica -> etiqueta
QUALITIES = [
    ('main', 'Principal (alta calidad)'),
    ('sub', 'Secundaria (baja calidad)'),
]

# Marcas que usan número de canal (útil para NVR/DVR con varias cámaras).
_NEEDS_CHANNEL = {'hikvision', 'dahua', 'reolink'}
# Marcas que muestran un campo de ruta RTSP manual.
_USES_CUSTOM_PATH = {'custom'}

DEFAULT_BRAND = 'tapo'
DEFAULT_PORT = 554


def brand_label(brand):
    """Etiqueta legible de una marca."""
    for key, label in BRANDS:
        if key == brand:
            return label
    return brand or DEFAULT_BRAND


def brand_needs_channel(brand):
    """True si la marca usa número de canal (NVR/DVR)."""
    return (brand or '').lower() in _NEEDS_CHANNEL


def brand_uses_custom_path(brand):
    """True si la marca usa una ruta RTSP escrita a mano."""
    return (brand or '').lower() in _USES_CUSTOM_PATH


def normalize_quality(cfg):
    """
    Devolver 'main' o 'sub' a partir de la config.
    Compatibilidad: cameras.json viejos solo tienen 'stream': 'stream1'/'stream2'.
    """
    quality = cfg.get('quality')
    if quality in ('main', 'sub'):
        return quality
    return 'sub' if str(cfg.get('stream', 'stream1')) == 'stream2' else 'main'


def quality_to_stream(quality):
    """Mapear 'main'/'sub' al campo legacy 'stream1'/'stream2'."""
    return 'stream2' if quality == 'sub' else 'stream1'


def build_path(brand, channel, quality):
    """
    Construir SOLO la ruta (lo que va después de :puerto/) según la marca.
    quality: 'main' | 'sub'. channel: entero (canal del NVR; 1 para IP suelta).
    """
    brand = (brand or DEFAULT_BRAND).lower()
    try:
        ch = int(channel)
    except (ValueError, TypeError):
        ch = 1
    if ch < 1:
        ch = 1

    if brand == 'hikvision':
        # 101 = canal 1 principal, 102 = canal 1 secundario, 201 = canal 2...
        sub = '01' if quality == 'main' else '02'
        return f"Streaming/Channels/{ch}{sub}"
    if brand == 'dahua':
        subtype = '0' if quality == 'main' else '1'
        return f"cam/realmonitor?channel={ch}&subtype={subtype}"
    if brand == 'reolink':
        suffix = 'main' if quality == 'main' else 'sub'
        return f"h264Preview_{ch:02d}_{suffix}"
    # tapo y fallback
    return 'stream1' if quality == 'main' else 'stream2'


def build_rtsp_url(cfg):
    """
    Construir la URL RTSP completa a partir de una config de cámara (dict).

    Maneja:
    - URL-encode de usuario y contraseña (Hikvision/Dahua suelen tener símbolos).
    - Marca 'custom': usa la ruta escrita a mano, o la URL completa si empieza con rtsp://.
    - Compatibilidad con cameras.json antiguos (sin 'brand', solo 'stream').

    Nunca lanza excepción: ante cualquier dato faltante usa valores por defecto.
    """
    try:
        brand = (cfg.get('brand') or DEFAULT_BRAND).lower()
        user = quote(str(cfg.get('username', '') or ''), safe='')
        pwd = quote(str(cfg.get('password', '') or ''), safe='')
        ip = str(cfg.get('ip', '') or '').strip()
        port = cfg.get('port', DEFAULT_PORT) or DEFAULT_PORT
        quality = normalize_quality(cfg)

        if brand_uses_custom_path(brand):
            raw = str(cfg.get('path', '') or '').strip()
            if raw.lower().startswith('rtsp://'):
                # El usuario pegó la URL completa: usarla tal cual.
                return raw
            path = raw.lstrip('/')
            return f"rtsp://{user}:{pwd}@{ip}:{port}/{path}"

        path = build_path(brand, cfg.get('channel', 1), quality)
        return f"rtsp://{user}:{pwd}@{ip}:{port}/{path}"
    except Exception:
        # Último recurso: formato Tapo clásico, sin encode.
        return (
            f"rtsp://{cfg.get('username', '')}:{cfg.get('password', '')}"
            f"@{cfg.get('ip', '')}:{cfg.get('port', DEFAULT_PORT)}/"
            f"{cfg.get('stream', 'stream1')}"
        )


def masked_rtsp_url(cfg):
    """Como build_rtsp_url pero ocultando la contraseña (para mostrar en pantalla)."""
    url = build_rtsp_url(cfg)
    pwd = str(cfg.get('password', '') or '')
    if pwd:
        encoded = quote(pwd, safe='')
        url = url.replace(':' + encoded + '@', ':****@').replace(':' + pwd + '@', ':****@')
    return url
