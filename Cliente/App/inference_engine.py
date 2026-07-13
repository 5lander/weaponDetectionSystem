# -*- coding: utf-8 -*-
"""
inference_engine.py - MOTOR DE INFERENCIA YOLO COMPARTIDO

En lugar de cargar el modelo YOLO una vez por cámara (N copias en RAM/VRAM),
se carga UNA sola vez y se comparte entre todas las cámaras mediante:
  - una cola central thread-safe de trabajos (camera_id),
  - un set de "último frame por cámara" (descarta frames viejos -> sin backlog),
  - uno o más workers (default 1) que ejecutan la inferencia por turnos y
    devuelven el resultado a la cámara correcta vía callback registrado por id.

El monitoreo NO se reduce: cada cámara registrada recibe SIEMPRE sus resultados
(enrutado por camera_id). Solo se comparte el modelo, no la cobertura.

Además instrumenta tiempos (inferencia y espera en cola) por cámara para poder
documentar el rendimiento real.
"""

import os
import sys
import csv
import time
import threading
import logging
from queue import Queue

import cv2
from ultralytics import YOLO

try:
    import GPUtil
except Exception:  # GPUtil es opcional
    GPUtil = None


def _app_dir():
    """Directorio base (compatible con PyInstaller frozen y desarrollo)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath('.')


class InferenceEngine:
    """Motor de inferencia compartido entre todas las cámaras."""

    _SENTINEL = object()

    def __init__(self, model_path, conf=0.5, iou=0.45, max_det=10,
                 num_workers=1, metrics_csv='inference_metrics.csv',
                 min_box_area_ratio=0.0):
        self.model_path = model_path
        self.conf = conf
        self.iou = iou
        self.max_det = max_det
        # Filtro anti-falsos-positivos: descarta cajas cuya área sea menor a
        # esta fracción del área total del frame (0.0 = sin filtro).
        self.min_box_area_ratio = max(0.0, float(min_box_area_ratio))
        self.num_workers = max(1, int(num_workers))

        self.model = None
        self.device = 'cpu'
        # Colores por clase (BGR) para candidate_multi.pt:
        #   0 Grenade, 1 Gun, 2 Knife, 3 Pistol, 4 handgun, 5 rifle
        # Armas de fuego en rojo, arma blanca en naranja, granada en amarillo.
        # Clases desconocidas caen al default (azul) vía .get().
        self.colors = {
            0: (0, 255, 255),   # Grenade  - amarillo
            1: (0, 0, 255),     # Gun      - rojo
            2: (0, 165, 255),   # Knife    - naranja
            3: (0, 0, 255),     # Pistol   - rojo
            4: (0, 0, 255),     # handgun  - rojo
            5: (0, 0, 255),     # rifle    - rojo
        }

        # Cola central + estado compartido (protegido por _lock)
        self._jobs = Queue()
        self._latest = {}        # camera_id -> (frame, submit_time)
        self._callbacks = {}     # camera_id -> callable(annotated_frame, detections)
        self._pending = set()    # camera_ids encolados y aún sin tomar (evita duplicados)
        self._inflight = set()   # camera_ids que un worker está procesando AHORA
        self._lock = threading.Lock()

        self._workers = []
        self._running = False

        # Métricas por cámara (protegidas por _metrics_lock)
        self._metrics = {}       # camera_id -> {'infer': [...], 'queue': [...], 'count': int}
        self._metrics_lock = threading.Lock()

        # CSV de métricas (para la tesis). Best-effort.
        self._metrics_csv_path = os.path.join(_app_dir(), metrics_csv) if metrics_csv else None
        self._csv_file = None
        self._csv_writer = None

    # ------------------------------------------------------------------ ciclo de vida
    def start(self):
        """Carga el modelo UNA sola vez y arranca el/los worker(s)."""
        if self._running:
            return
        logging.info(f"[Engine] Cargando modelo (1 sola vez): {self.model_path}")
        self.model = YOLO(self.model_path)
        try:
            self.model.fuse()  # fusiona capas (1 sola vez)
        except Exception as e:
            logging.warning(f"[Engine] fuse() falló, continúo: {e}")

        self.device = '0' if self._detect_gpu() else 'cpu'
        self._open_metrics_csv()

        self._running = True
        for i in range(self.num_workers):
            t = threading.Thread(target=self._run, name=f"InferenceWorker-{i}", daemon=True)
            t.start()
            self._workers.append(t)

        logging.info(f"[Engine] Listo. device={self.device}, workers={self.num_workers}")

    def stop(self, timeout=5):
        """Apagado limpio: detiene workers (sentinela) y libera el modelo."""
        if not self._running and not self._workers:
            return
        self._running = False
        for _ in self._workers:
            self._jobs.put(self._SENTINEL)
        for t in self._workers:
            t.join(timeout=timeout)
        self._workers = []
        self.model = None
        self._close_metrics_csv()
        logging.info("[Engine] Detenido y modelo liberado")

    def _detect_gpu(self):
        # IMPORTANTE: no basta con que exista una GPU física (GPUtil/nvidia-smi)
        # ni con que torch tenga CUDA. torchvision TAMBIÉN debe tener sus ops
        # (NMS) compiladas para CUDA. Un caso real muy común: torch '+cu118' pero
        # torchvision '+cpu' -> torchvision.ops.nms en GPU lanza
        # NotImplementedError ("Could not run 'torchvision::nms' ... 'CUDA'") y
        # TODA inferencia falla. Por eso probamos una NMS mínima REAL en CUDA:
        # si funciona, usamos GPU; si no, caemos a CPU (lento pero estable).
        try:
            import torch
            if not torch.cuda.is_available():
                return False
            import torchvision
            boxes = torch.tensor([[0.0, 0.0, 1.0, 1.0]], device='cuda')
            scores = torch.tensor([0.5], device='cuda')
            torchvision.ops.nms(boxes, scores, 0.5)  # si esto no lanza, GPU sirve
            return True
        except Exception as e:
            logging.warning(
                f"[Engine] GPU presente pero no usable para inferencia "
                f"({type(e).__name__}: {e}). Usando CPU. "
                f"Para GPU, alinear torchvision con la build CUDA de torch."
            )
            return False

    # ------------------------------------------------------------------ registro / envío
    def register(self, camera_id, callback):
        """Registrar el callback de una cámara. Garantiza que esa cámara recibirá sus resultados."""
        with self._lock:
            self._callbacks[camera_id] = callback
        with self._metrics_lock:
            self._metrics.setdefault(camera_id, {'infer': [], 'queue': [], 'count': 0})
        logging.info(f"[Engine] Cámara {camera_id} registrada")

    def unregister(self, camera_id):
        """Quitar una cámara (al detenerla) para no entregarle resultados ya muerta."""
        with self._lock:
            self._callbacks.pop(camera_id, None)
            self._latest.pop(camera_id, None)
            self._pending.discard(camera_id)
        logging.info(f"[Engine] Cámara {camera_id} dada de baja")

    def submit(self, camera_id, frame):
        """Encolar el frame más reciente de una cámara (descarta el anterior sin procesar)."""
        if not self._running:
            return
        with self._lock:
            self._latest[camera_id] = (frame, time.time())
            # Encolar solo si no está ya pendiente NI siendo procesado por un worker.
            # Esto evita que (con num_workers>1) dos workers procesen la misma cámara
            # en paralelo. Los frames que lleguen mientras está en proceso solo
            # actualizan _latest; al terminar, el worker re-encola si hay uno más nuevo.
            if camera_id not in self._pending and camera_id not in self._inflight:
                self._pending.add(camera_id)
                self._jobs.put(camera_id)

    # ------------------------------------------------------------------ worker
    def _run(self):
        """Loop del worker: toma un camera_id, analiza su frame más reciente y entrega el resultado."""
        logging.info(f"[Engine] Worker iniciado: {threading.current_thread().name}")
        while True:
            cid = self._jobs.get()
            if cid is self._SENTINEL:
                break

            with self._lock:
                self._pending.discard(cid)
                # Si otro worker ya está procesando esta cámara, no la dupliques.
                if cid in self._inflight:
                    continue
                item = self._latest.get(cid)
                callback = self._callbacks.get(cid)
                if item is None or callback is None:
                    continue
                # Reservar la cámara: solo UN worker la procesa a la vez.
                self._inflight.add(cid)
                frame, submit_time = item

            queue_wait = time.time() - submit_time
            t0 = time.time()
            try:
                annotated, detections = self._infer(frame)
                infer_time = time.time() - t0
                self._record_metrics(cid, infer_time, queue_wait)
                # El callback corre en el hilo del worker (NO en el hilo Qt).
                # DetectionTapo solo emite señales (thread-safe) y guarda/sube.
                callback(annotated, detections)
            except Exception as e:
                # logging.exception conserva el traceback completo (antes solo
                # el mensaje). Cubre TODO el path posterior a la detección:
                # _infer + callback -> on_inference_result -> saveDetection.
                logging.exception(f"[Engine] Error procesando cámara {cid}: {e}")
            finally:
                with self._lock:
                    self._inflight.discard(cid)
                    # Si llegó un frame MÁS NUEVO mientras procesábamos, re-encolar
                    # (para no perder el frame más reciente bajo carga).
                    latest = self._latest.get(cid)
                    if (latest is not None and latest[1] > submit_time
                            and cid not in self._pending and cid in self._callbacks):
                        self._pending.add(cid)
                        self._jobs.put(cid)

        logging.info(f"[Engine] Worker detenido: {threading.current_thread().name}")

    def _infer(self, frame):
        """Inferencia YOLO + dibujo de recuadros. Device cacheado (no GPUtil por frame)."""
        results = self.model(
            frame,
            verbose=False,
            conf=self.conf,
            iou=self.iou,
            max_det=self.max_det,
            half=False,
            device=self.device
        )

        # Área del frame para el filtro de tamaño mínimo de caja.
        frame_area = frame.shape[0] * frame.shape[1]

        detected = []
        for result in results:
            for box in result.boxes:
                conf = float(box.conf[0])
                cls = int(box.cls[0])

                # Filtro de tamaño: descartar cajas demasiado pequeñas (ruido).
                if self.min_box_area_ratio > 0 and frame_area > 0:
                    bx1, by1, bx2, by2 = box.xyxy[0].tolist()
                    box_area = max(0.0, (bx2 - bx1)) * max(0.0, (by2 - by1))
                    if (box_area / frame_area) < self.min_box_area_ratio:
                        continue

                detected.append({
                    'class': cls,
                    'confidence': conf,
                    'box': box.xyxy[0].tolist()
                })
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                color = self.colors.get(cls, (255, 0, 0))
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                label = f"{self.model.names[cls]} {conf:.2f}"
                cv2.putText(frame, label, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        return frame, detected

    # ------------------------------------------------------------------ métricas (FASE 2)
    def _record_metrics(self, camera_id, infer_time, queue_wait):
        with self._metrics_lock:
            m = self._metrics.setdefault(camera_id, {'infer': [], 'queue': [], 'count': 0})
            m['infer'].append(infer_time)
            m['queue'].append(queue_wait)
            m['count'] += 1
        logging.info(
            f"[Metrics] cam={camera_id} inferencia={infer_time * 1000:.1f}ms "
            f"cola={queue_wait * 1000:.1f}ms"
        )
        self._write_metrics_csv(camera_id, infer_time, queue_wait)

    def get_metrics_summary(self):
        """Resumen consultable por cámara: count + promedio/min/max de inferencia y cola (ms)."""
        out = {}
        with self._metrics_lock:
            for cid, m in self._metrics.items():
                inf, q = m['infer'], m['queue']
                if inf:
                    out[cid] = {
                        'count': m['count'],
                        'infer_avg_ms': 1000 * sum(inf) / len(inf),
                        'infer_min_ms': 1000 * min(inf),
                        'infer_max_ms': 1000 * max(inf),
                        'queue_avg_ms': 1000 * sum(q) / len(q),
                        'queue_min_ms': 1000 * min(q),
                        'queue_max_ms': 1000 * max(q),
                    }
                else:
                    out[cid] = {'count': 0}
        return out

    def _open_metrics_csv(self):
        if not self._metrics_csv_path:
            return
        try:
            new_file = not os.path.exists(self._metrics_csv_path)
            self._csv_file = open(self._metrics_csv_path, 'a', newline='', encoding='utf-8')
            self._csv_writer = csv.writer(self._csv_file)
            if new_file:
                self._csv_writer.writerow(['timestamp', 'camera_id', 'inferencia_ms', 'cola_ms'])
                self._csv_file.flush()
            logging.info(f"[Engine] Métricas CSV: {self._metrics_csv_path}")
        except Exception as e:
            logging.warning(f"[Engine] No se pudo abrir CSV de métricas: {e}")
            self._csv_file = None
            self._csv_writer = None

    def _write_metrics_csv(self, camera_id, infer_time, queue_wait):
        if not self._csv_writer:
            return
        try:
            with self._metrics_lock:
                self._csv_writer.writerow([
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                    camera_id,
                    f"{infer_time * 1000:.1f}",
                    f"{queue_wait * 1000:.1f}",
                ])
                self._csv_file.flush()
        except Exception:
            pass

    def _close_metrics_csv(self):
        try:
            if self._csv_file:
                self._csv_file.close()
        except Exception:
            pass
        finally:
            self._csv_file = None
            self._csv_writer = None
