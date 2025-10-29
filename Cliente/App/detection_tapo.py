# -*- coding: utf-8 -*-
"""
detection_tapo.py - VERSIÓN ULTRA OPTIMIZADA PARA TAPO C310
Máxima velocidad, mínima latencia, soporte multi-cámara
"""

import os
import sys
import threading
import time
from queue import Queue, Empty
from collections import deque
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QImage
import cv2
from ultralytics import YOLO
import numpy as np
import psutil
import GPUtil
import requests
import logging

class DetectionTapo(QThread):
    """
    Clase ULTRA OPTIMIZADA para cámaras Tapo C310
    - Multi-threading avanzado
    - Colas sin buffer (latencia < 500ms)
    - Procesamiento asíncrono
    - Recuperación automática de errores
    """
    changePixmap = pyqtSignal(QImage)
    resourceUpdate = pyqtSignal(dict)
    error = pyqtSignal(str)
    weaponDetected = pyqtSignal(str)
    statusUpdate = pyqtSignal(str)
    
    def __init__(self, model_path, token, location, receiver, camera_config, camera_id=1):
        super(DetectionTapo, self).__init__()
        
        # Identificación
        self.camera_id = camera_id
        self.camera_name = camera_config.get('name', f'Camera {camera_id}')
        
        # Configuración básica
        self.model_path = model_path
        self.colors = {0: (0, 0, 255), 1: (0, 165, 255)}
        self.token = token
        self.location = location
        self.receiver = receiver
        
        # Configuración de cámara
        self.camera_config = camera_config
        self.rtsp_url = self._build_rtsp_url()
        
        # Control de ejecución
        self.running = False
        self.cap = None
        self.model = None
        
        # OPTIMIZACIÓN: Intervalos ajustados para máxima velocidad
        self.analysis_interval = 2  # Analizar cada 2 segundos (antes 3)
        self.last_analysis_time = 0
        self.capture_interval = 4   # Enviar detecciones cada 4 segundos (antes 5)
        self.last_capture_time = 0
        self.resource_check_interval = 10  # Verificar recursos cada 10s (antes 5)
        self.last_resource_check = 0
        
        # OPTIMIZACIÓN: Sistema de colas sin buffer (máximo 1 frame pendiente)
        self.frame_queue = Queue(maxsize=1)
        self.analysis_queue = Queue(maxsize=1)
        
        # OPTIMIZACIÓN: Threads independientes
        self.capture_thread = None
        self.analysis_thread = None
        self.analysis_running = False
        
        # OPTIMIZACIÓN: Frame skipping inteligente
        self.frame_counter = 0
        self.skip_frames = 0  # Procesar todos los frames para UI
        
        # OPTIMIZACIÓN: Pool de frames para reutilización
        self.frame_pool = deque(maxlen=3)
        
        # Métricas de rendimiento
        self.fps_counter = 0
        self.fps_timer = time.time()
        self.current_fps = 0
        
        # Recuperación de errores
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 3
        self.reconnect_delay = 2
        
        logging.info(f"[Cámara {self.camera_id}] DetectionTapo OPTIMIZADA inicializada")
        logging.info(f"[Cámara {self.camera_id}] Ubicación: {self.location}")
    
    def _build_rtsp_url(self):
        """Construir URL RTSP optimizada"""
        cfg = self.camera_config
        username = cfg.get('username', 'admin')
        password = cfg.get('password', '')
        ip = cfg.get('ip')
        port = cfg.get('port', 554)
        stream = cfg.get('stream', 'stream1')
        
        return f"rtsp://{username}:{password}@{ip}:{port}/{stream}"
    
    def run(self):
        """Thread principal de ejecución OPTIMIZADO"""
        self.running = True
        
        # Cargar modelo YOLO una sola vez
        if not self._load_model():
            return
        
        # Inicializar cámara con máxima optimización
        if not self._initialize_rtsp_camera_optimized():
            return
        
        # OPTIMIZACIÓN: Iniciar threads de captura y análisis
        self._start_capture_thread()
        self._start_analysis_thread()
        
        # OPTIMIZACIÓN: Loop principal solo para UI (máxima responsividad)
        retry_count = 0
        max_retries = 3
        
        while self.running:
            try:
                # OPTIMIZACIÓN: Obtener frame de la cola sin bloquear
                try:
                    frame = self.frame_queue.get(timeout=0.05)
                    retry_count = 0
                    
                    # Actualizar UI inmediatamente
                    self.update_ui(frame)
                    
                    # Actualizar FPS
                    self._update_fps()
                    
                    # Enviar a análisis cada N segundos
                    current_time = time.time()
                    if (current_time - self.last_analysis_time) >= self.analysis_interval:
                        self._queue_frame_for_analysis(frame.copy())
                        self.last_analysis_time = current_time
                    
                    # Verificar recursos (menos frecuente)
                    if (current_time - self.last_resource_check) >= self.resource_check_interval:
                        self.check_resources()
                        self.last_resource_check = current_time
                    
                except Empty:
                    retry_count += 1
                    if retry_count > max_retries:
                        self.statusUpdate.emit(f"[Cámara {self.camera_id}] Sin frames")
                        time.sleep(0.1)
                        retry_count = 0
                    continue
                
            except Exception as e:
                logging.error(f"[Cámara {self.camera_id}] Error en loop principal: {e}")
                break
        
        self.cleanup()
    
    def _load_model(self):
        """Cargar modelo YOLO con optimizaciones"""
        try:
            self.model = YOLO(self.model_path)
            
            # OPTIMIZACIÓN: Configurar modelo para inferencia rápida
            self.model.fuse()  # Fusionar capas para velocidad
            
            logging.info(f"[Cámara {self.camera_id}] Modelo YOLO cargado y optimizado")
            return True
        except Exception as e:
            error_msg = f"[Cámara {self.camera_id}] Error al cargar YOLO: {str(e)}"
            self.error.emit(error_msg)
            logging.error(error_msg)
            self.running = False
            return False
    
    def _initialize_rtsp_camera_optimized(self):
        """Inicializar cámara RTSP con MÁXIMA OPTIMIZACIÓN"""
        try:
            # OPTIMIZACIÓN CRÍTICA: Variables de entorno FFmpeg
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
                "rtsp_transport;udp|"           # UDP para mínima latencia
                "fflags;nobuffer+fastseek+flush_packets|"  # Sin buffer
                "flags;low_delay|"              # Baja latencia
                "max_delay;0|"                  # Sin delay
                "reorder_queue_size;0|"         # Sin reordenamiento
                "buffer_size;0|"                # Sin buffer extra
                "probesize;32|"                 # Detección rápida
                "analyzeduration;0|"            # Sin análisis
                "sync;ext"                      # Sincronización externa
            )
            
            logging.info(f"[Cámara {self.camera_id}] Conectando a {self.camera_config['ip']}...")
            
            # Abrir con FFmpeg backend
            self.cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
            
            if not self.cap.isOpened():
                # Intento 2: TCP si UDP falla
                logging.warning(f"[Cámara {self.camera_id}] UDP falló, intentando TCP...")
                os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
                    "rtsp_transport;tcp|"
                    "fflags;nobuffer|"
                    "flags;low_delay"
                )
                self.cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
            
            if self.cap.isOpened():
                # OPTIMIZACIÓN: Configuraciones críticas
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)     # Buffer mínimo
                self.cap.set(cv2.CAP_PROP_FPS, 15)           # Tapo C310 = 15fps
                
                # Obtener info
                width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                logging.info(f"[Cámara {self.camera_id}] ✅ Conectada - {width}x{height}")
                self.statusUpdate.emit(f"[Cámara {self.camera_id}] Conectada")
                return True
            
            error_msg = f"[Cámara {self.camera_id}] ❌ No se pudo abrir stream RTSP"
            self.error.emit(error_msg)
            logging.error(error_msg)
            self.running = False
            return False
            
        except Exception as e:
            error_msg = f"[Cámara {self.camera_id}] Error al inicializar: {str(e)}"
            self.error.emit(error_msg)
            logging.error(error_msg)
            self.running = False
            return False
    
    def _start_capture_thread(self):
        """Iniciar thread de captura ULTRA RÁPIDO"""
        self.capture_thread = threading.Thread(
            target=self._capture_worker_optimized, 
            daemon=True,
            name=f"Capture-Cam{self.camera_id}"
        )
        self.capture_thread.start()
        logging.info(f"[Cámara {self.camera_id}] Thread de captura iniciado")
    
    def _capture_worker_optimized(self):
        """Worker de captura OPTIMIZADO para máxima velocidad"""
        logging.info(f"[Cámara {self.camera_id}] Captura worker iniciado")
        
        consecutive_failures = 0
        max_failures = 5
        
        while self.running:
            try:
                # OPTIMIZACIÓN: Captura directa sin validaciones pesadas
                ret, frame = self.cap.read()
                
                if not ret:
                    consecutive_failures += 1
                    if consecutive_failures > max_failures:
                        logging.error(f"[Cámara {self.camera_id}] Demasiados fallos de captura")
                        self._attempt_reconnect()
                        consecutive_failures = 0
                    time.sleep(0.05)
                    continue
                
                consecutive_failures = 0
                
                # OPTIMIZACIÓN: Sin bloqueo - si la cola está llena, descartar frame viejo
                if self.frame_queue.full():
                    try:
                        self.frame_queue.get_nowait()
                    except:
                        pass
                
                # Agregar frame más reciente
                self.frame_queue.put_nowait(frame)
                
            except Exception as e:
                logging.error(f"[Cámara {self.camera_id}] Error en capture worker: {e}")
                time.sleep(0.1)
        
        logging.info(f"[Cámara {self.camera_id}] Captura worker detenido")
    
    def _attempt_reconnect(self):
        """Intentar reconectar cámara"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            error_msg = f"[Cámara {self.camera_id}] Máximo de reintentos alcanzado"
            self.error.emit(error_msg)
            self.running = False
            return
        
        self.reconnect_attempts += 1
        logging.info(f"[Cámara {self.camera_id}] Reintentando conexión ({self.reconnect_attempts}/{self.max_reconnect_attempts})...")
        
        if self.cap:
            self.cap.release()
        
        time.sleep(self.reconnect_delay)
        
        if self._initialize_rtsp_camera_optimized():
            self.reconnect_attempts = 0
            logging.info(f"[Cámara {self.camera_id}] Reconexión exitosa")
    
    def _start_analysis_thread(self):
        """Iniciar thread de análisis YOLO"""
        self.analysis_running = True
        self.analysis_thread = threading.Thread(
            target=self._analysis_worker_optimized, 
            daemon=True,
            name=f"Analysis-Cam{self.camera_id}"
        )
        self.analysis_thread.start()
        logging.info(f"[Cámara {self.camera_id}] Thread de análisis iniciado")
    
    def _analysis_worker_optimized(self):
        """Worker de análisis OPTIMIZADO"""
        logging.info(f"[Cámara {self.camera_id}] Análisis worker iniciado")
        
        while self.analysis_running:
            try:
                if self.analysis_queue.empty():
                    time.sleep(0.1)
                    continue
                
                frame = self.analysis_queue.get(timeout=1)
                
                # OPTIMIZACIÓN: Análisis YOLO con configuración rápida
                self._analyze_frame_fast(frame)
                
            except Empty:
                continue
            except Exception as e:
                logging.error(f"[Cámara {self.camera_id}] Error en análisis: {e}")
                time.sleep(0.1)
        
        logging.info(f"[Cámara {self.camera_id}] Análisis worker detenido")
    
    def _queue_frame_for_analysis(self, frame):
        """Agregar frame a cola de análisis SIN BLOQUEO"""
        try:
            if self.analysis_queue.full():
                try:
                    self.analysis_queue.get_nowait()
                except:
                    pass
            self.analysis_queue.put_nowait(frame)
        except:
            pass
    
    def _analyze_frame_fast(self, frame):
        """Análisis YOLO OPTIMIZADO"""
        try:
            # OPTIMIZACIÓN: Inferencia rápida
            results = self.model(
                frame,
                verbose=False,
                conf=0.5,           # Confianza mínima
                iou=0.45,           # IoU para NMS
                max_det=10,         # Máximo 10 detecciones
                half=False,         # Usar FP16 si tienes GPU
                device='0' if self._has_gpu() else 'cpu'
            )
            
            detected_objects = []
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    
                    detected_objects.append({
                        'class': cls,
                        'confidence': conf,
                        'box': box.xyxy[0].tolist()
                    })
                    
                    # Dibujar en frame
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), 
                                self.colors.get(cls, (255, 0, 0)), 2)
                    
                    label = f"{self.model.names[cls]} {conf:.2f}"
                    cv2.putText(frame, label, (x1, y1-10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, 
                              self.colors.get(cls, (255, 0, 0)), 2)
            
            if detected_objects:
                msg = f"[Cámara {self.camera_id}] {len(detected_objects)} objetos detectados"
                logging.info(msg)
                self.weaponDetected.emit(msg)
                
                # Guardar y enviar
                current_time = time.time()
                if (current_time - self.last_capture_time) >= self.capture_interval:
                    self.saveDetection(frame, detected_objects)
                    self.last_capture_time = current_time
                    
        except Exception as e:
            logging.error(f"[Cámara {self.camera_id}] Error en análisis YOLO: {e}")
    
    def _has_gpu(self):
        """Verificar si hay GPU disponible"""
        try:
            gpus = GPUtil.getGPUs()
            return len(gpus) > 0
        except:
            return False
    
    def update_ui(self, frame):
        """Actualizar UI OPTIMIZADO"""
        try:
            # OPTIMIZACIÓN: Conversión rápida de color
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            
            # Crear QImage
            qt_image = QImage(
                rgb_image.data, w, h, bytes_per_line, 
                QImage.Format_RGB888
            )
            
            # OPTIMIZACIÓN: Escalar con transformación rápida
            scaled = qt_image.scaled(
                640, 480, 
                Qt.KeepAspectRatio, 
                Qt.FastTransformation  # Transformación rápida
            )
            
            self.changePixmap.emit(scaled)
            
        except Exception as e:
            logging.error(f"[Cámara {self.camera_id}] Error al actualizar UI: {e}")
    
    def _update_fps(self):
        """Actualizar contador de FPS"""
        self.fps_counter += 1
        current_time = time.time()
        
        if current_time - self.fps_timer >= 1.0:
            self.current_fps = self.fps_counter / (current_time - self.fps_timer)
            self.statusUpdate.emit(
                f"[Cámara {self.camera_id}] {self.current_fps:.1f} FPS"
            )
            self.fps_counter = 0
            self.fps_timer = current_time
    
    def check_resources(self):
        """Verificar recursos del sistema"""
        try:
            resource_data = {
                'camera_id': self.camera_id,
                'cpu': psutil.cpu_percent(),
                'memory': psutil.virtual_memory().percent,
                'fps': self.current_fps
            }
            
            # GPU info si disponible
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    resource_data['gpu_load'] = gpus[0].load * 100
                    resource_data['gpu_memory'] = gpus[0].memoryUtil * 100
            except:
                pass
            
            self.resourceUpdate.emit(resource_data)
            
        except Exception as e:
            logging.error(f"[Cámara {self.camera_id}] Error al verificar recursos: {e}")
    
    def saveDetection(self, frame, detections):
        """Guardar detección"""
        try:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            filename = f"detection_cam{self.camera_id}_{self.location}_{timestamp}.jpg"
            filepath = os.path.join("detections", filename)
            
            os.makedirs("detections", exist_ok=True)
            cv2.imwrite(filepath, frame)
            
            logging.info(f"[Cámara {self.camera_id}] Detección guardada: {filename}")
            
            # Enviar al servidor (asíncrono)
            threading.Thread(
                target=self._upload_to_server, 
                args=(filepath, detections),
                daemon=True
            ).start()
            
        except Exception as e:
            logging.error(f"[Cámara {self.camera_id}] Error al guardar detección: {e}")
    
    def _upload_to_server(self, filepath, detections):
        """Subir detección al servidor"""
        try:
            url = 'http://tu-servidor.com/api/upload'
            
            files = {'image': open(filepath, 'rb')}
            data = {
                'token': self.token,
                'location': self.location,
                'receiver': self.receiver,
                'camera_id': self.camera_id,
                'detections': str(detections)
            }
            
            response = requests.post(url, files=files, data=data, timeout=10)
            
            if response.status_code == 200:
                logging.info(f"[Cámara {self.camera_id}] Enviado al servidor")
            else:
                logging.error(f"[Cámara {self.camera_id}] Error servidor: {response.status_code}")
                
        except Exception as e:
            logging.error(f"[Cámara {self.camera_id}] Error al enviar: {e}")
    
    def cleanup(self):
        """Limpiar recursos"""
        logging.info(f"[Cámara {self.camera_id}] Limpiando recursos...")
        
        self.analysis_running = False
        
        # Esperar threads
        if self.analysis_thread and self.analysis_thread.is_alive():
            self.analysis_thread.join(timeout=2)
        
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=2)
        
        # Limpiar colas
        for queue in [self.analysis_queue, self.frame_queue]:
            while not queue.empty():
                try:
                    queue.get_nowait()
                except:
                    break
        
        # Liberar cámara
        if self.cap:
            self.cap.release()
        
        logging.info(f"[Cámara {self.camera_id}] Recursos liberados")
    
    def stop(self):
        """Detener detección"""
        self.running = False
        self.analysis_running = False
        logging.info(f"[Cámara {self.camera_id}] Deteniendo...")