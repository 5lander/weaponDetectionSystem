# -*- coding: utf-8 -*-
import os
import sys
import threading
import time
from queue import Queue
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QImage
import cv2
from ultralytics import YOLO
import numpy as np
import psutil
import GPUtil
import requests
import logging

class Detection(QThread):
    changePixmap = pyqtSignal(QImage)
    resourceUpdate = pyqtSignal(dict)
    error = pyqtSignal(str)
    weaponDetected = pyqtSignal(str)
    
    def __init__(self, model_path, token, location, receiver):
        super(Detection, self).__init__()
        self.model_path = model_path
        self.colors = {0: (0, 0, 255), 1: (0, 165, 255)}
        self.last_resource_check = 0
        self.resource_check_interval = 5
        self.token = token
        self.location = location
        self.receiver = receiver
        
        # Configuración optimizada MANTENIENDO el análisis original
        self.analysis_interval = 3  # Analizar cada 3 segundos
        self.last_analysis_time = 0
        self.capture_interval = 5  # Enviar detecciones cada 5 segundos
        self.last_capture_time = 0
        
        self.model = None
        self.running = False
        self.cap = None
        
        # Cola para frames a analizar
        self.analysis_queue = Queue(maxsize=2)
        self.analysis_thread = None
        self.analysis_running = False
        
        logging.info("Instancia de Detection con análisis original inicializada")

    def run(self):
        self.running = True
        
        # Cargar modelo
        try:
            self.model = YOLO(self.model_path)
            logging.info("Modelo YOLO cargado exitosamente.")
        except Exception as e:
            error_msg = f"Error al cargar el modelo YOLO: {str(e)}"
            self.error.emit(error_msg)
            logging.error(error_msg)
            self.running = False
            return

        # Inicializar cámara
        if not self._initialize_camera():
            return
            
        # Iniciar hilo de análisis
        self._start_analysis_thread()
        
        # Loop principal para video
        retry_count = 0
        max_retries = 5
        
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                retry_count += 1
                if retry_count > max_retries:
                    error_msg = "Error: No se pudo leer el frame de la cámara después de varios intentos."
                    self.error.emit(error_msg)
                    logging.error(error_msg)
                    break
                time.sleep(0.1)
                continue
            
            retry_count = 0
            
            # Siempre actualizar UI para video fluido
            self.update_ui(frame)
            
            # Enviar frame para análisis cada 3 segundos
            current_time = time.time()
            if (current_time - self.last_analysis_time) >= self.analysis_interval:
                self._queue_frame_for_analysis(frame.copy())
                self.last_analysis_time = current_time
            
            # Verificar recursos
            self.check_resources()
            
            # Pequeña pausa para no sobrecargar CPU
            time.sleep(0.033)  # ~30 FPS

        self.cleanup()

    def _initialize_camera(self):
        """Inicializar cámara con diferentes backends"""
        backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
        for backend in backends:
            self.cap = cv2.VideoCapture(0 + backend)
            if self.cap.isOpened():
                # Configurar cámara para mejor rendimiento
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
                logging.info(f"Cámara abierta con backend: {backend}")
                return True
        
        error_msg = "Error: No se pudo abrir la cámara con ningún backend."
        self.error.emit(error_msg)
        logging.error(error_msg)
        self.running = False
        return False

    def _start_analysis_thread(self):
        """Iniciar hilo separado para análisis de frames"""
        self.analysis_running = True
        self.analysis_thread = threading.Thread(target=self._analysis_worker, daemon=True)
        self.analysis_thread.start()
        logging.info("Hilo de análisis iniciado")

    def _queue_frame_for_analysis(self, frame):
        """Agregar frame a la cola de análisis"""
        try:
            # Si la cola está llena, remover el frame más antiguo
            if self.analysis_queue.full():
                try:
                    self.analysis_queue.get_nowait()
                except:
                    pass
            
            self.analysis_queue.put_nowait(frame)
        except Exception as e:
            logging.warning(f"Error al agregar frame a cola de análisis: {e}")

    def _analysis_worker(self):
        """Worker thread para análisis de frames"""
        logging.info("Worker de análisis iniciado")
        
        while self.analysis_running:
            try:
                # Esperar por un frame con timeout
                frame = self.analysis_queue.get(timeout=1)
                
                if frame is not None:
                    self._analyze_frame(frame)
                    
            except Exception as e:
                if self.analysis_running:  # Solo log si no estamos cerrando
                    logging.debug(f"Timeout o error en análisis: {e}")
                continue

    def _analyze_frame(self, frame):
        """Analizar frame con YOLO - MANTENIENDO LÓGICA ORIGINAL"""
        try:
            # USAR LA LÓGICA ORIGINAL QUE FUNCIONABA BIEN
            results = self.model(frame, verbose=False)
            
            detection_made = False
            detected_objects = []
            
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    conf = box.conf[0]
                    cls = int(box.cls[0])
                    
                    if conf > 0.5:  # UMBRAL ORIGINAL
                        detection_made = True
                        object_name = self.model.names[cls]
                        detected_objects.append(f"{object_name} ({conf:.2f})")
                        
                        # Dibujar detección en frame para guardado - COMO ESTABA ANTES
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        color = self.colors.get(cls, (255, 255, 255))
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        label = f'{object_name} {conf:.2f}'
                        cv2.putText(frame, label, (x1, y1 - 10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
            
            # Si hay detección, procesar
            if detection_made:
                # Emitir señal de detección para notificación
                objects_str = ", ".join(detected_objects)
                self.weaponDetected.emit(f"¡Arma detectada! {objects_str}")
                
                # Guardar y enviar si es tiempo
                current_time = time.time()
                if (current_time - self.last_capture_time) >= self.capture_interval:
                    self.saveDetection(frame)
                    self.last_capture_time = current_time
                    
        except Exception as e:
            error_msg = f"Error durante el análisis del frame: {str(e)}"
            self.error.emit(error_msg)
            logging.error(error_msg)

    def update_ui(self, frame):
        """Actualizar UI con frame de video"""
        try:
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            convert_to_qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            p = convert_to_qt_format.scaled(640, 480, Qt.KeepAspectRatio)
            self.changePixmap.emit(p)
        except Exception as e:
            logging.error(f"Error al actualizar UI: {e}")

    def check_resources(self):
        """Verificar recursos del sistema"""
        current_time = time.time()
        if current_time - self.last_resource_check >= self.resource_check_interval:
            try:
                cpu_percent = psutil.cpu_percent()
                memory_percent = psutil.virtual_memory().percent
                
                gpu_info = {}
                try:
                    gpus = GPUtil.getGPUs()
                    if gpus:
                        gpu = gpus[0]
                        gpu_info = {
                            'gpu_load': gpu.load * 100,
                            'gpu_memory': gpu.memoryUsed / gpu.memoryTotal * 100
                        }
                except Exception as e:
                    logging.warning(f"Error al obtener información de la GPU: {str(e)}")

                resources = {
                    'cpu': cpu_percent,
                    'memory': memory_percent,
                    **gpu_info
                }
                
                self.resourceUpdate.emit(resources)
                logging.debug(f"Recursos actualizados: CPU {cpu_percent:.1f}%, Memoria {memory_percent:.1f}%")
            except Exception as e:
                error_msg = f"Error al monitorear recursos: {str(e)}"
                self.error.emit(error_msg)
                logging.error(error_msg)
            
            self.last_resource_check = current_time

    def saveDetection(self, frame):
        """Guardar frame con detección - Solo mantener 1 archivo"""
        try:
            save_path = self.resource_path("savedFrame")
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            
            # USAR SIEMPRE EL MISMO NOMBRE DE ARCHIVO para sobrescribir
            filename = "current_detection.jpg"
            full_path = os.path.join(save_path, filename)
            
            # Eliminar archivo anterior si existe (opcional, cv2.imwrite ya sobrescribe)
            if os.path.exists(full_path):
                try:
                    os.remove(full_path)
                    logging.debug("Archivo anterior eliminado")
                except:
                    pass  # No importa si no se puede eliminar
            
            cv2.imwrite(full_path, frame)
            logging.info(f'Frame guardado (sobrescrito): {filename}')
            
            # Enviar en hilo separado para no bloquear
            threading.Thread(target=self.postDetection, args=(full_path,), daemon=True).start()
            
        except Exception as e:
            error_msg = f"Error al guardar la detección: {str(e)}"
            self.error.emit(error_msg)
            logging.error(error_msg)

    def postDetection(self, image_path):
        """Enviar detección al servidor"""
        try:
            url = 'https://weaponnotificationserver.onrender.com/api/images/'
            headers = {'Authorization': 'Token ' + self.token}
            
            with open(image_path, 'rb') as img_file:
                files = {'image': img_file}
                data = {'userID': self.token, 'location': self.location, 'alertReceiver': self.receiver}
                
                response = requests.post(url, files=files, headers=headers, data=data, timeout=30)

            if response.ok:
                logging.info('Alerta enviada al servidor exitosamente')
            else:
                error_msg = f'Error al enviar alerta. Código: {response.status_code}'
                self.error.emit(error_msg)
                logging.error(error_msg)
                
        except requests.exceptions.Timeout:
            error_msg = 'Timeout al conectar con el servidor'
            self.error.emit(error_msg)
            logging.error(error_msg)
        except requests.exceptions.ConnectionError:
            error_msg = 'Error de conexión con el servidor'
            self.error.emit(error_msg)
            logging.error(error_msg)
        except Exception as e:
            error_msg = f'Error al acceder al servidor: {str(e)}'
            self.error.emit(error_msg)
            logging.error(error_msg)

    def cleanup(self):
        """Limpiar recursos"""
        # Detener hilo de análisis
        self.analysis_running = False
        if self.analysis_thread and self.analysis_thread.is_alive():
            self.analysis_thread.join(timeout=2)
        
        # Limpiar cola
        while not self.analysis_queue.empty():
            try:
                self.analysis_queue.get_nowait()
            except:
                break
        
        # Liberar cámara
        if self.cap:
            self.cap.release()
            
        logging.info("Recursos liberados correctamente")

    def stop(self):
        """Detener detección"""
        self.running = False
        self.analysis_running = False
        logging.info("Deteniendo detección")

    def resource_path(self, relative_path):
        """Obtener ruta de recurso"""
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)