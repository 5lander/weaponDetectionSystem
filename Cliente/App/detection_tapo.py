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
    
    def __init__(self, model_path, token, location, receiver, camera_config, camera_id=1, engine=None):
        super(DetectionTapo, self).__init__()

        # Identificación
        self.camera_id = camera_id
        self.camera_name = camera_config.get('name', f'Camera {camera_id}')

        # Configuración básica
        self.model_path = model_path
        self.token = token
        self.location = location
        self.receiver = receiver

        # Motor de inferencia COMPARTIDO (1 modelo para todas las cámaras).
        # La inferencia ya no ocurre en esta clase: se delega al engine.
        self.engine = engine

        # Configuración de cámara
        self.camera_config = camera_config
        # Fuente local (webcam USB / laptop) vs cámara IP RTSP
        from .rtsp_profiles import is_local_source, local_device_index
        self.is_local = is_local_source(camera_config)
        self.local_index = local_device_index(camera_config)
        self.rtsp_url = self._build_rtsp_url()

        # Control de ejecución
        self.running = False
        self.cap = None

        # OPTIMIZACIÓN: Intervalos ajustados para máxima velocidad
        self.analysis_interval = 2  # Enviar frame a análisis cada 2 segundos
        self.last_analysis_time = 0
        self.capture_interval = 4   # Enviar detecciones cada 4 segundos
        self.last_capture_time = 0

        # CONFIRMACIÓN TEMPORAL (anti-falsos-positivos) tipo "N de las últimas M":
        # el arma debe verse en al menos N de los últimos M ciclos de análisis
        # antes de guardar/alertar. Tolera el parpadeo de confianza del modelo
        # (mejor que exigir frames perfectamente seguidos) y a la vez un falso
        # positivo de un solo frame (celular, mano, sombra) no genera evidencia.
        from .cameras_config import GLOBAL_CONFIG, box_area_limits, scene_label

        # Ventana de tamaño de caja propia de esta cámara (según su escenario).
        # Se resuelve aquí, una sola vez, y se entrega al motor al registrarse.
        self.min_box_area_ratio, self.max_box_area_ratio = box_area_limits(camera_config)
        logging.info(
            f"[Cámara {camera_id}] Escenario: {scene_label(camera_config.get('scene'))} "
            f"-> caja admitida {self.min_box_area_ratio * 100:.3f}% a "
            f"{self.max_box_area_ratio * 100:.1f}% del encuadre"
        )

        self.confirmation_frames = max(1, int(GLOBAL_CONFIG.get('confirmation_frames', 1)))
        self.confirmation_window = max(self.confirmation_frames,
                                       int(GLOBAL_CONFIG.get('confirmation_window',
                                                             self.confirmation_frames)))
        # Ventana deslizante de resultados recientes (True=hubo detección).
        self._recent_hits = deque(maxlen=self.confirmation_window)
        self.resource_check_interval = 10  # Verificar recursos cada 10s
        self.last_resource_check = 0

        # Cola de captura sin buffer (máximo 1 frame pendiente) para el video en vivo
        self.frame_queue = Queue(maxsize=1)

        # Thread de captura (el de análisis ya no existe: lo maneja el engine)
        self.capture_thread = None

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
        """Construir URL RTSP según la marca de la cámara (Tapo, Hikvision, Dahua, etc.)."""
        from .rtsp_profiles import build_rtsp_url
        return build_rtsp_url(self.camera_config)
    
    def run(self):
        """Thread principal de ejecución OPTIMIZADO"""
        self.running = True

        # Inicializar cámara con máxima optimización
        if not self._initialize_rtsp_camera_optimized():
            return

        # Registrar esta cámara en el motor de inferencia compartido para
        # recibir SIEMPRE los resultados de sus propias capturas (por camera_id).
        # Se le pasan los límites de tamaño de caja de ESTA cámara (según su
        # escenario), porque el tamaño que ocupa un arma en el encuadre depende
        # de la distancia a la que está colocada.
        if self.engine:
            self.engine.register(
                self.camera_id, self.on_inference_result,
                min_box_area_ratio=self.min_box_area_ratio,
                max_box_area_ratio=self.max_box_area_ratio,
            )

        # Iniciar SOLO el thread de captura (el análisis lo hace el engine)
        self._start_capture_thread()

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
                    
                    # Enviar frame al motor de inferencia compartido cada N segundos
                    current_time = time.time()
                    if (current_time - self.last_analysis_time) >= self.analysis_interval:
                        if self.engine:
                            self.engine.submit(self.camera_id, frame.copy())
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

    def _initialize_local_camera(self):
        """Inicializar una webcam local (USB / cámara de la laptop) por índice."""
        try:
            logging.info(f"[Cámara {self.camera_id}] Abriendo webcam local (índice {self.local_index})...")

            # En Windows, DirectShow abre la webcam mucho más rápido y estable.
            if sys.platform.startswith('win'):
                self.cap = cv2.VideoCapture(self.local_index, cv2.CAP_DSHOW)
            else:
                self.cap = cv2.VideoCapture(self.local_index)

            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                logging.info(f"[Cámara {self.camera_id}] ✅ Webcam local conectada - {width}x{height}")
                self.statusUpdate.emit(f"[Cámara {self.camera_id}] Webcam local conectada")
                return True

            error_msg = f"[Cámara {self.camera_id}] ❌ No se pudo abrir la webcam local (índice {self.local_index})"
            self.error.emit(error_msg)
            logging.error(error_msg)
            self.running = False
            return False

        except Exception as e:
            error_msg = f"[Cámara {self.camera_id}] Error al abrir webcam local: {str(e)}"
            self.error.emit(error_msg)
            logging.error(error_msg)
            self.running = False
            return False

    def _initialize_rtsp_camera_optimized(self):
        """Inicializar cámara RTSP con MÁXIMA OPTIMIZACIÓN"""
        try:
            # Fuente local (webcam USB / laptop): abrir por índice, sin FFmpeg/RTSP.
            if self.is_local:
                return self._initialize_local_camera()

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
    
    def on_inference_result(self, annotated_frame, detections):
        """Callback que invoca el motor de inferencia con el resultado de ESTA cámara.

        Corre en el hilo del worker del engine (NO en el hilo Qt). Es seguro porque:
        - emitir señales Qt entre hilos es thread-safe (conexión en cola),
        - saveDetection solo escribe un archivo y lanza su propio hilo de subida
          (no toca widgets),
        - last_capture_time lo escribe solo este callback (worker único por cámara).
        """
        # Registrar el resultado de este ciclo en la ventana deslizante.
        # (Este callback siempre se invoca; con detecciones=hit, sin ellas=miss.)
        self._recent_hits.append(bool(detections))
        hits = sum(self._recent_hits)

        if not detections:
            return

        # Confirmación temporal "N de M": solo alertar si el arma se vio en al
        # menos N de los últimos M ciclos. Filtra el falso positivo aislado.
        if hits < self.confirmation_frames:
            logging.info(
                f"[Cámara {self.camera_id}] Detección sin confirmar "
                f"({hits}/{self.confirmation_frames} en últimas {len(self._recent_hits)}) - se espera persistencia"
            )
            return

        msg = f"[Cámara {self.camera_id}] {len(detections)} objetos detectados"
        logging.info(msg)

        # Guardar y enviar (rate-limitado por capture_interval), igual que antes.
        # La señal weaponDetected (que incrementa el contador de la UI) se emite
        # SOLO cuando realmente se guarda y envía al servidor, para que el
        # contador coincida 1:1 con los envíos/registros del servidor (antes se
        # emitía en cada ciclo de inferencia ~cada 2s, por eso la UI mostraba
        # más detecciones que imágenes enviadas).
        current_time = time.time()
        if (current_time - self.last_capture_time) >= self.capture_interval:
            self.saveDetection(annotated_frame, detections)
            self.last_capture_time = current_time
            self.weaponDetected.emit(msg)
    
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
            # URL del servidor: la que declare settings.ini / GLOBAL_CONFIG.
            # Antes estaba hardcodeada aqui, asi que editar settings.ini no tenia
            # ningun efecto sobre las subidas (solo sobre el resto de la app).
            from .cameras_config import GLOBAL_CONFIG
            url = GLOBAL_CONFIG.get(
                'server_url',
                'https://weaponnotificationserver.onrender.com/api/images/')
            
            # Los nombres DEBEN coincidir con el serializer del servidor
            # (UploadAlertSerializer): userID (= token), location, alertReceiver, image.
            headers = {'Authorization': 'Token ' + str(self.token)}
            with open(filepath, 'rb') as img_file:
                files = {'image': img_file}
                data = {
                    'userID': self.token,
                    'location': self.location,
                    'alertReceiver': self.receiver,
                }

                # Confianza de la deteccion mas fuerte del frame (0.0 - 1.0).
                # El servidor la guarda en UploadAlert y la muestra en el correo.
                try:
                    confidences = [float(d.get('confidence', 0)) for d in (detections or [])]
                    if confidences:
                        data['confidence'] = round(max(confidences), 4)
                except (TypeError, ValueError):
                    pass
                # TIMEOUT: el servidor corre en el plan gratuito de Render, que
                # APAGA la instancia tras un rato sin trafico. El primer request
                # despues de ese apagado tarda ~30-60 s en responder (arranque en
                # frio) mientras los siguientes van en ~1 s. Con el timeout de 10 s
                # que habia antes, la PRIMERA alerta fallaba siempre y en silencio:
                # se registraba el error en el log y no se reintentaba, asi que la
                # deteccion nunca llegaba al servidor. Se separa el timeout de
                # conexion (10 s, detecta un host caido rapido) del de lectura
                # (90 s, tolera el arranque en frio).
                response = requests.post(url, files=files, data=data,
                                         headers=headers, timeout=(10, 90))

            if response.status_code == 200:
                logging.info(f"[Cámara {self.camera_id}] Enviado al servidor")
            else:
                logging.error(f"[Cámara {self.camera_id}] Error servidor: {response.status_code} {response.text[:200]}")
                
        except Exception as e:
            logging.error(f"[Cámara {self.camera_id}] Error al enviar: {e}")
    
    def cleanup(self):
        """Limpiar recursos"""
        logging.info(f"[Cámara {self.camera_id}] Limpiando recursos...")

        # Dar de baja del motor de inferencia (deja de recibir resultados)
        if self.engine:
            self.engine.unregister(self.camera_id)

        # Esperar thread de captura
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=2)

        # Limpiar cola de captura
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except Empty:
                break

        # Liberar cámara
        if self.cap:
            self.cap.release()

        logging.info(f"[Cámara {self.camera_id}] Recursos liberados")

    def stop(self):
        """Detener detección"""
        self.running = False
        # Dar de baja del engine de inmediato para no entregar resultados a una cámara detenida
        if self.engine:
            self.engine.unregister(self.camera_id)
        logging.info(f"[Cámara {self.camera_id}] Deteniendo...")