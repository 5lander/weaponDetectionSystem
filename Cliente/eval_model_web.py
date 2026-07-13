# -*- coding: utf-8 -*-
"""
eval_model_web.py - Evalúa el modelo con imágenes REALES de armas de internet.

Como no siempre se puede tener un arma física para probar, este script descarga
imágenes de licencia libre (personas con pistolas / cuchillos) y mide a qué
confianza las detecta el modelo. Sirve para:
  - Calibrar la clase handGun (pistola) sin arma real.
  - Juzgar objetivamente si el modelo está "muy mal" o es usable.

Guarda las imágenes anotadas en  eval_web/  y un resumen por consola.
"""

import os
import sys
import json
import urllib.request
import urllib.parse

import cv2
from ultralytics import YOLO


def _here():
    return os.path.dirname(os.path.abspath(__file__))


MODEL_PATH = os.path.join(_here(), "model", "last.pt")
OUT_DIR = os.path.join(_here(), "eval_web")
CONF_DIAG = 0.15  # umbral bajo: ver TODO lo que el modelo piensa

# Búsquedas en Wikimedia Commons (licencia libre). En vez de adivinar URLs,
# preguntamos a la API por un término y usamos la imagen que devuelva.
# formato: (nombre, término_de_búsqueda, clase_esperada)
IMAGES = [
    ("pistola_1", "pistol handgun", "handGun"),
    ("pistola_disparo", "person shooting pistol", "handGun"),
    ("pistola_glock", "Glock pistol", "handGun"),
    ("pistola_mano", "hand holding gun", "handGun"),
    ("cuchillo_1", "knife hand", "knife"),
    ("cuchillo_cocina", "kitchen knife", "knife"),
    # Negativos: NO hay arma -> el modelo NO debería detectar nada
    ("negativo_celular", "person holding smartphone", "NADA"),
    ("negativo_persona", "man portrait face", "NADA"),
]

# Wikimedia bloquea urllib por defecto: hace falta User-Agent de navegador.
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
API = "https://commons.wikimedia.org/w/api.php"


def _http_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()


def resolve_image_url(term):
    """Devuelve la URL (thumb 640px) de la primera imagen que Commons dé para el término."""
    q = urllib.parse.urlencode({
        "action": "query", "generator": "search", "gsrsearch": term,
        "gsrlimit": "1", "gsrnamespace": "6", "prop": "imageinfo",
        "iiprop": "url", "iiurlwidth": "640", "format": "json",
    })
    data = json.loads(_http_get(API + "?" + q).decode("utf-8"))
    pages = data.get("query", {}).get("pages", {})
    for _, page in pages.items():
        info = page.get("imageinfo", [{}])[0]
        return info.get("thumburl") or info.get("url")
    return None


def download(url, dest):
    with open(dest, "wb") as f:
        f.write(_http_get(url))


def main():
    # Permite comparar modelos:  python eval_model_web.py <ruta_al_.pt>
    model_path = sys.argv[1] if len(sys.argv) > 1 else MODEL_PATH
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"[Eval] Cargando modelo: {model_path}")
    model = YOLO(model_path)
    print(f"[Eval] CLASES: {model.names}\n")

    print("=" * 70)
    print(f"{'imagen':22} {'esperado':10} {'-> detectó (clase conf area%)'}")
    print("=" * 70)

    for name, term, expected in IMAGES:
        raw = os.path.join(OUT_DIR, name + "_orig.jpg")
        # Cache: si ya bajamos la imagen antes, la reusamos (evita 429 y compara
        # modelos sobre EXACTAMENTE las mismas imágenes).
        if not (os.path.exists(raw) and os.path.getsize(raw) > 0):
            try:
                url = resolve_image_url(term)
                if not url:
                    print(f"{name:22} {expected:10} -> [sin resultado para '{term}']")
                    continue
                download(url, raw)
            except Exception as e:
                print(f"{name:22} {expected:10} -> [descarga falló: {e}]")
                continue

        img = cv2.imread(raw)
        if img is None:
            print(f"{name:22} {expected:10} -> [no se pudo leer la imagen]")
            continue

        h, w = img.shape[:2]
        area = float(h * w)
        results = model(img, verbose=False, conf=CONF_DIAG, iou=0.45, device="cpu")

        dets = []
        for result in results:
            for box in result.boxes:
                c = float(box.conf[0])
                cls = int(box.cls[0])
                cname = model.names[cls]
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                apct = 100.0 * max(0.0, x2 - x1) * max(0.0, y2 - y1) / area
                dets.append((cname, c, apct))
                color = (0, 0, 255) if c >= 0.6 else (0, 200, 255) if c >= 0.4 else (150, 150, 150)
                cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                cv2.putText(img, f"{cname} {c:.2f}", (int(x1), max(0, int(y1) - 6)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        cv2.imwrite(os.path.join(OUT_DIR, name + "_anotada.jpg"), img)

        if dets:
            dets.sort(key=lambda d: -d[1])
            resumen = ", ".join(f"{cn} {c:.2f} ({a:.0f}%)" for cn, c, a in dets[:4])
        else:
            resumen = "NADA detectado"
        print(f"{name:22} {expected:10} -> {resumen}")

    print("=" * 70)
    print(f"\n[Eval] Imágenes anotadas en: {OUT_DIR}")


if __name__ == "__main__":
    main()
