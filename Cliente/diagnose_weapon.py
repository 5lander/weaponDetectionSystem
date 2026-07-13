# -*- coding: utf-8 -*-
"""
diagnose_weapon.py - MODO DIAGNÓSTICO del modelo de detección de armas.

Objetivo: VER qué hace realmente tu modelo, sin filtros que oculten nada.
Corre la inferencia con un umbral MUY BAJO (0.15) para mostrar TODO lo que el
modelo cree ver, con su clase y su nivel de confianza. Así podemos decidir el
umbral correcto o confirmar si el modelo necesita ayuda.

USO:
    python diagnose_weapon.py            # webcam índice 0
    python diagnose_weapon.py 1          # webcam índice 1
    python diagnose_weapon.py 0 0.10     # webcam 0, umbral 0.10

CONTROLES (con la ventana de video enfocada):
    [ESPACIO]  -> guarda la foto actual (con las cajas) + registra los números
    [g]        -> marca la foto como "ESTOY con el arma"  (para revisar detección)
    [n]        -> marca la foto como "SIN arma"           (para revisar falsos +)
    [q]        -> salir

Todo se guarda en la carpeta  diagnostico/  :
    - imágenes anotadas  (cajas + confianza)
    - registro.csv       (números por cada foto: clase, confianza, tamaño de caja)

Luego yo (Claude) reviso esas imágenes y el CSV y te digo qué umbral usar.
"""

import os
import sys
import csv
import time

import cv2
from ultralytics import YOLO


# ---------------------------------------------------------------- configuración
def _here():
    return os.path.dirname(os.path.abspath(__file__))


MODEL_PATH = os.path.join(_here(), "model", "last.pt")
OUT_DIR = os.path.join(_here(), "diagnostico")

CONF_DIAG = 0.15   # umbral BAJO a propósito: queremos ver TODO lo que ve el modelo
IOU = 0.45


def main():
    # Argumentos flexibles: cualquier token .pt = modelo; números = cam y umbral.
    #   python diagnose_weapon.py                          -> last.pt, cam 0
    #   python diagnose_weapon.py model/candidate_multi.pt -> probar otro modelo
    #   python diagnose_weapon.py model/candidate_multi.pt 1 0.25
    model_path = MODEL_PATH
    nums = []
    for a in sys.argv[1:]:
        if a.lower().endswith(".pt"):
            model_path = a if os.path.isabs(a) else os.path.join(_here(), a)
        else:
            nums.append(a)
    cam_index = int(nums[0]) if len(nums) > 0 else 0
    conf = float(nums[1]) if len(nums) > 1 else CONF_DIAG

    os.makedirs(OUT_DIR, exist_ok=True)

    print(f"[Diag] Cargando modelo: {model_path}")
    model = YOLO(model_path)
    print(f"[Diag] CLASES DEL MODELO: {model.names}")

    # Forzamos CPU: en este equipo torch trae CUDA pero torchvision es CPU-only,
    # así que la NMS en GPU falla ('torchvision::nms' not for CUDA backend).
    # Para el diagnóstico por webcam, CPU va sobrado.
    device = "cpu"
    print(f"[Diag] device={device} | umbral diagnóstico={conf}")

    # Probar varios backends: DirectShow suele decir "abierto" aunque no dé
    # frames; MSMF o el backend por defecto a veces sí funcionan.
    backends = []
    if sys.platform.startswith("win"):
        backends = [("CAP_DSHOW", cv2.CAP_DSHOW), ("CAP_MSMF", cv2.CAP_MSMF), ("default", 0)]
    else:
        backends = [("default", 0)]

    cap = None
    for name, be in backends:
        print(f"[Diag] Abriendo webcam índice {cam_index} con backend {name}...", flush=True)
        cap_try = cv2.VideoCapture(cam_index, be) if be else cv2.VideoCapture(cam_index)
        if not cap_try.isOpened():
            print(f"[Diag]   -> {name}: no abrió.", flush=True)
            cap_try.release()
            continue
        # Warm-up: algunas cámaras necesitan unos reads antes de dar frame bueno.
        ok = False
        for _ in range(10):
            r, f = cap_try.read()
            if r and f is not None:
                ok = True
                break
            time.sleep(0.1)
        if ok:
            print(f"[Diag]   -> {name}: OK, entregando frames {f.shape[1]}x{f.shape[0]}.", flush=True)
            cap = cap_try
            break
        print(f"[Diag]   -> {name}: abrió pero NO entrega frames.", flush=True)
        cap_try.release()

    if cap is None:
        print(f"\n[Diag] ERROR: la webcam índice {cam_index} no entrega imagen con ningún backend.", flush=True)
        print("       Causas comunes:", flush=True)
        print("         - Otra app está usando la cámara (Zoom/Teams/Meet/navegador). Ciérrala.", flush=True)
        print("         - Falta permiso: Config. de Windows > Privacidad > Cámara > permitir apps de escritorio.", flush=True)
        print("         - Es otro índice. Prueba:  python diagnose_weapon.py 1   (o 2)", flush=True)
        return

    # Registro de números para revisar después
    csv_path = os.path.join(OUT_DIR, "registro.csv")
    new_file = not os.path.exists(csv_path)
    csv_file = open(csv_path, "a", newline="", encoding="utf-8")
    writer = csv.writer(csv_file)
    if new_file:
        writer.writerow(["foto", "marca", "clase", "confianza", "area_pct", "box_xyxy"])

    print("\n=== CONTROLES ===")
    print("  [ESPACIO] guardar foto   [g] con arma   [n] sin arma   [q] salir\n")
    print("Sal con el cuchillo/arma en distintas posiciones y pulsa [g].")
    print("Luego, SIN el arma, pulsa [n] un par de veces (para ver falsos positivos).\n")

    shot = 0
    last_mark = "?"
    win = "DIAGNOSTICO - modelo de armas (pulsa q para salir)"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)

    frames = 0
    fail_streak = 0
    print("[Diag] Ventana abierta. Si no la ves, búscala en la barra de tareas.", flush=True)

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            fail_streak += 1
            if fail_streak % 20 == 1:
                print(f"[Diag] La cámara dejó de dar frames (x{fail_streak})...", flush=True)
            if fail_streak > 200:
                print("[Diag] Demasiados fallos seguidos, cierro.", flush=True)
                break
            time.sleep(0.05)
            continue
        fail_streak = 0

        frames += 1
        if frames % 60 == 0:  # latido: confirma que sigue vivo
            print(f"[Diag] ...vivo, {frames} frames procesados, {shot} fotos guardadas.", flush=True)

        h, w = frame.shape[:2]
        frame_area = float(h * w)

        results = model(frame, verbose=False, conf=conf, iou=IOU, device=device)

        dets = []
        annotated = frame.copy()
        for result in results:
            for box in result.boxes:
                c = float(box.conf[0])
                cls = int(box.cls[0])
                name = model.names.get(cls, str(cls)) if isinstance(model.names, dict) else model.names[cls]
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                area_pct = 100.0 * max(0.0, x2 - x1) * max(0.0, y2 - y1) / frame_area
                dets.append((name, c, area_pct, [round(x1), round(y1), round(x2), round(y2)]))

                # Color por confianza: rojo=alta, amarillo=media, gris=baja
                if c >= 0.6:
                    color = (0, 0, 255)
                elif c >= 0.4:
                    color = (0, 200, 255)
                else:
                    color = (150, 150, 150)
                cv2.rectangle(annotated, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                cv2.putText(annotated, f"{name} {c:.2f} ({area_pct:.1f}%)",
                            (int(x1), max(0, int(y1) - 8)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # Info en pantalla
        info = f"detecciones: {len(dets)}  |  umbral diag: {conf:.2f}  |  [g] con arma  [n] sin arma  [ESPACIO] guardar"
        cv2.putText(annotated, info, (10, h - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        cv2.imshow(win, annotated)
        key = cv2.waitKey(1) & 0xFF

        # Si cerraron la ventana con la X, salir limpio.
        try:
            if cv2.getWindowProperty(win, cv2.WND_PROP_VISIBLE) < 1:
                print("[Diag] Ventana cerrada.", flush=True)
                break
        except cv2.error:
            break

        if key == ord("q"):
            break
        elif key in (ord("g"), ord("n"), ord(" ")):
            if key == ord("g"):
                last_mark = "CON_ARMA"
            elif key == ord("n"):
                last_mark = "SIN_ARMA"
            else:
                last_mark = "SPACE"

            shot += 1
            fname = f"diag_{shot:03d}_{last_mark}.jpg"
            fpath = os.path.join(OUT_DIR, fname)
            cv2.imwrite(fpath, annotated)

            if dets:
                for (name, c, area_pct, boxxy) in dets:
                    writer.writerow([fname, last_mark, name, f"{c:.3f}", f"{area_pct:.2f}", boxxy])
                    print(f"  [{fname}] {last_mark:8} -> {name} conf={c:.3f} area={area_pct:.1f}%")
            else:
                writer.writerow([fname, last_mark, "NINGUNA", "", "", ""])
                print(f"  [{fname}] {last_mark:8} -> SIN DETECCIONES")
            csv_file.flush()

    cap.release()
    cv2.destroyAllWindows()
    csv_file.close()
    print(f"\n[Diag] Listo. {shot} fotos guardadas en: {OUT_DIR}")
    print(f"[Diag] Registro de números: {csv_path}")


if __name__ == "__main__":
    main()
