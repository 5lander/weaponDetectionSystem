import os
import sys
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QMutex, QMutexLocker
from PyQt5.QtGui import QImage
import cv2
import time
from ultralytics import YOLO
import numpy as np
import psutil
import GPUtil
import requests
import logging
import gc
from threading import Event

class Detection(QThread):
    changePixmap = pyqtSignal(QImage)
    resourceUpdate = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, model_path, token, location, receiver):
        super(Detection, self).__init__()
        
        # Parámetros principales
        self.model_path = model_path
        self.token = token
        self.location = location
        self.receiver = receiver
        
        # Configuración de detección
        self.colors = {0: (0, 0, 255), 1: (0, 165, 255)}
        self.frame_skip = 3
        self.frame_count = 0
        
        # Control de tiempo
        self.last_resource_check = 0
        self.resource_check_interval = 5
        self.last_capture_time = 0
        self.capture_interval = 5
        
        # Variables de control thread-safe
        self.running = False
        self._stop_event = Event()
        self._mutex = QMutex()
        
        # Recursos
        self.model = None
        self.cap = None
        
        # Control de errores
        self._max_consecutive_errors = 5
        self._consecutive_errors = 0
        
        logging.info("Instancia de Detection inicializada de forma segura")

    def run(self):
        """Método principal del hilo con manejo robusto de errores"""
        try:
            self._initialize_detection()
            if not self.running:
                return
                
            self._main_detection_loop()
            
        except Exception as e:
            error_msg = f"Error crítico en el hilo de detección: {str(e)}"
            self.error.emit(error_msg)
            logging.error(error_msg)
        finally:
            self._safe_cleanup()

    def _initialize_detection(self):
        """Inicializa el modelo y la cámara de forma segura"""
        with QMutexLocker(self._mutex):
            self.running = True
            self._stop_event.clear()
        
        # Cargar modelo YOLO
        if not self._load_model():
            return
            
        # Inicializar cámara
        if not self._initialize_camera():
            return
            
        logging.info("Detection inicializada correctamente")

    def _load_model(self):
        """Carga el modelo YOLO con manejo de errores"""
        try:
            if not os.path.exists(self.model_path):
                error_msg = f"Archivo de modelo no encontrado: {self.model_path}"
                self.error.emit(error_msg)
                logging.error(error_msg)
                return False
                
            self.model = YOLO(self.model_path)
            logging.info("Modelo YOLO cargado exitosamente.")
            return True
            
        except Exception as e:
            error_msg = f"Error al cargar el modelo YOLO: {str(e)}"
            self.error.emit(error_msg)
            logging.error(error_msg)
            with QMutexLocker(self._mutex):
                self.running = False
            return False

    def _initialize_camera(self):
        """Inicializa la cámara con diferentes backends"""
        backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
        
        for backend in backends:
            if self._stop_event.is_set():
                return False
                
            try:
                self.cap = cv2.VideoCapture(0, backend)
                if self.cap and self.cap.isOpened():
                    # Configurar parámetros de la cámara
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    self.cap.set(cv2.CAP_PROP_FPS, 30)
                    
                    # Verificar que realmente funciona
                    ret, test_frame = self.cap.read()
                    if ret and test_frame is not None:
                        logging.info(f"Cámara abierta con backend: {backend}")
                        return True
                    else:
                        self.cap.release()
                        self.cap = None
                        
            except Exception as e:
                logging.warning(f"Error con backend {backend}: {e}")
                if self.cap:
                    self.cap.release()
                    self.cap = None
        
        error_msg = "Error: No se pudo abrir la cámara con ningún backend."
        self.error.emit(error_msg)
        logging.error(error_msg)
        with QMutexLocker(self._mutex):
            self.running = False
        return False

    def _main_detection_loop(self):
        """Bucle principal de detección con control robusto"""
        retry_count = 0
        max_retries = 5

        while self.running and not self._stop_event.is_set():
            try:
                # Verificar si debemos parar
                if self._stop_event.wait(0.001):  # Timeout muy pequeño
                    break
                
                # Leer frame de la cámara
                ret, frame = self._read_frame_safely()
                
                if not ret or frame is None:
                    retry_count += 1
                    if retry_count > max_retries:
                        error_msg = "Error: No se pudo leer el frame de la cámara después de varios intentos."
                        self.error.emit(error_msg)
                        logging.error(error_msg)
                        break
                    time.sleep(0.1)
                    continue
                
                retry_count = 0
                self._consecutive_errors = 0

                # Procesar frame
                self.frame_count += 1
                if self.frame_count % self.frame_skip == 0:
                    self._process_frame_safely(frame)

                # Actualizar UI
                self._update_ui_safely(frame)
                
                # Verificar recursos del sistema
                self._check_resources_safely()

            except Exception as e:
                self._consecutive_errors += 1
                error_msg = f"Error en bucle principal: {str(e)}"
                logging.error(error_msg)
                
                if self._consecutive_errors >= self._max_consecutive_errors:
                    self.error.emit(f"Demasiados errores consecutivos: {error_msg}")
                    break
                    
                time.sleep(0.5)  # Pausa antes de continuar

    def _read_frame_safely(self):
        """Lee un frame de la cámara de forma segura"""
        if not self.cap or not self.cap.isOpened():
            return False, None
            
        try:
            return self.cap.read()
        except Exception as e:
            logging.error(f"Error leyendo frame: {e}")
            return False, None

    def _process_frame_safely(self, frame):
        """Procesa el frame con detección de armas de forma segura"""
        if self._stop_event.is_set() or not self.model:
            return
            
        try:
            # Realizar detección
            results = self.model(frame, verbose=False)
            
            detection_made = False
            for r in results:
                if self._stop_event.is_set():
                    break
                    
                boxes = r.boxes
                if boxes is None:
                    continue
                    
                for box in boxes:
                    try:
                        conf = float(box.conf[0])
                        cls = int(box.cls[0])

                        if conf > 0.75:
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            color = self.colors.get(cls, (255, 255, 255))
                            
                            # Dibujar rectángulo y etiqueta
                            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                            label = f'{self.model.names[cls]} {conf:.2f}'
                            cv2.putText(frame, label, (x1, y1 - 10), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
                            detection_made = True
                            
                    except Exception as e:
                        logging.warning(f"Error procesando detección individual: {e}")
                        continue

            # Guardar detección si es necesaria
            if detection_made and not self._stop_event.is_set():
                current_time = time.time()
                if (current_time - self.last_capture_time) >= self.capture_interval:
                    self._save_detection_safely(frame)
                    self.last_capture_time = current_time

        except Exception as e:
            logging.error(f"Error en procesamiento de frame: {e}")

    def _update_ui_safely(self, frame):
        """Actualiza la UI de forma segura"""
        if self._stop_event.is_set():
            return
            
        try:
            # Convertir a formato Qt
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            
            convert_to_qt_format = QImage(
                rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888
            )
            
            # Escalar imagen
            scaled_image = convert_to_qt_format.scaled(640, 480, Qt.KeepAspectRatio)
            
            # Emitir solo si no estamos parando
            if not self._stop_event.is_set():
                self.changePixmap.emit(scaled_image)
                
        except Exception as e:
            logging.error(f"Error actualizando UI: {e}")

    def _check_resources_safely(self):
        """Verifica recursos del sistema de forma segura"""
        if self._stop_event.is_set():
            return
            
        current_time = time.time()
        if current_time - self.last_resource_check < self.resource_check_interval:
            return
            
        try:
            # Obtener información de CPU y memoria
            cpu_percent = psutil.cpu_percent(interval=None)
            memory_percent = psutil.virtual_memory().percent
            
            # Obtener información de GPU
            gpu_info = self._get_gpu_info_safely()
            
            resources = {
                'cpu': cpu_percent,
                'memory': memory_percent,
                **gpu_info
            }
            
            # Emitir solo si no estamos parando
            if not self._stop_event.is_set():
                self.resourceUpdate.emit(resources)
                
            self.last_resource_check = current_time
            
            logging.debug(f"Recursos: CPU {cpu_percent:.1f}%, "
                         f"Memoria {memory_percent:.1f}%, "
                         f"GPU {gpu_info.get('gpu_load', 'N/A')}")
            
        except Exception as e:
            logging.error(f"Error monitoreando recursos: {e}")

    def _get_gpu_info_safely(self):
        """Obtiene información de GPU de forma segura"""
        gpu_info = {}
        try:
            gpus = GPUtil.getGPUs()
            if gpus and len(gpus) > 0:
                gpu = gpus[0]
                gpu_info = {
                    'gpu_load': gpu.load * 100,
                    'gpu_memory': gpu.memoryUsed / gpu.memoryTotal * 100 if gpu.memoryTotal > 0 else 0
                }
        except Exception as e:
            logging.warning(f"Error obteniendo información de GPU: {e}")
            gpu_info = {'gpu_load': 0, 'gpu_memory': 0}
        
        return gpu_info

    def _save_detection_safely(self, frame):
        """Guarda la detección de forma segura"""
        if self._stop_event.is_set():
            return
            
        try:
            save_path = self.resource_path("savedFrame")
            if not os.path.exists(save_path):
                os.makedirs(save_path, exist_ok=True)
                
            frame_path = os.path.join(save_path, "frame.jpg")
            success = cv2.imwrite(frame_path, frame)
            
            if success:
                logging.info('Frame guardado exitosamente')
                # Enviar detección al servidor en hilo separado
                self._post_detection_async()
            else:
                logging.error('Error guardando frame')
                
        except Exception as e:
            error_msg = f"Error guardando detección: {str(e)}"
            logging.error(error_msg)
            if not self._stop_event.is_set():
                self.error.emit(error_msg)

    def _post_detection_async(self):
        """Envía la detección al servidor de forma asíncrona"""
        if self._stop_event.is_set():
            return
            
        try:
            url = 'https://weapondetectionsystem.onrender.com/api/images/'
            headers = {'Authorization': 'Token ' + self.token}
            
            frame_path = self.resource_path('savedFrame/frame.jpg')
            if not os.path.exists(frame_path):
                logging.error("Archivo de frame no encontrado para envío")
                return
            
            with open(frame_path, 'rb') as f:
                files = {'image': f}
                data = {
                    'userID': self.token, 
                    'location': self.location, 
                    'alertReceiver': self.receiver
                }
                
                response = requests.post(
                    url, files=files, headers=headers, data=data, timeout=10
                )

            if response.ok:
                logging.info('Alerta enviada al servidor exitosamente')
            else:
                error_msg = f'Error enviando alerta. Código: {response.status_code}'
                logging.error(error_msg)
                
        except requests.exceptions.Timeout:
            logging.error('Timeout al conectar con el servidor')
        except requests.exceptions.ConnectionError:
            logging.error('Error de conexión con el servidor')
        except Exception as e:
            error_msg = f'Error accediendo al servidor: {str(e)}'
            logging.error(error_msg)

    def stop(self):
        """Detiene el hilo de detección de forma segura"""
        logging.info("Iniciando parada segura del hilo de detección")
        
        with QMutexLocker(self._mutex):
            self.running = False
            
        # Señalar parada
        self._stop_event.set()
        
        # Esperar un momento para que el hilo procese la señal
        time.sleep(0.1)

    def _safe_cleanup(self):
        """Limpia recursos de forma segura"""
        logging.info("Iniciando limpieza segura de recursos")
        
        try:
            # Limpiar cámara
            if self.cap:
                try:
                    self.cap.release()
                    self.cap = None
                    logging.info("Cámara liberada")
                except Exception as e:
                    logging.error(f"Error liberando cámara: {e}")
            
            # Limpiar modelo
            if self.model:
                try:
                    del self.model
                    self.model = None
                    logging.info("Modelo YOLO limpiado")
                except Exception as e:
                    logging.error(f"Error limpiando modelo: {e}")
            
            # Forzar recolección de basura
            gc.collect()
            
            logging.info("Limpieza de recursos completada")
            
        except Exception as e:
            logging.error(f"Error durante limpieza: {e}")

    def resource_path(self, relative_path):
        """Obtiene la ruta del recurso de forma segura"""
        try:
            if hasattr(sys, '_MEIPASS'):
                return os.path.join(sys._MEIPASS, relative_path)
            return os.path.join(os.path.abspath("."), relative_path)
        except Exception as e:
            logging.error(f"Error obteniendo ruta del recurso: {e}")
            return relative_path

    def __del__(self):
        """Destructor para limpieza final"""
        try:
            self.stop()
            self._safe_cleanup()
        except Exception as e:
            logging.error(f"Error en destructor: {e}")