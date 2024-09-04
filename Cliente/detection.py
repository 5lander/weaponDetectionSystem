import os
import sys
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QImage
import cv2
import time
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

    def __init__(self, model_path, token, location, receiver):
        super(Detection, self).__init__()
        self.model_path = model_path
        self.colors = {0: (0, 0, 255), 1: (0, 165, 255)}
        self.last_resource_check = 0
        self.resource_check_interval = 5
        self.token = token
        self.location = location
        self.receiver = receiver
        self.last_capture_time = 0
        self.capture_interval = 5
        self.frame_skip = 3
        self.frame_count = 0
        self.model = None
        self.running = False
        self.cap = None
        logging.info("Instancia de Detection inicializada")

    def run(self):
        self.running = True
        
        try:
            self.model = YOLO(self.model_path)
            logging.info("Modelo YOLO cargado exitosamente.")
        except Exception as e:
            error_msg = f"Error al cargar el modelo YOLO: {str(e)}"
            self.error.emit(error_msg)
            logging.error(error_msg)
            self.running = False
            return

        backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
        for backend in backends:
            self.cap = cv2.VideoCapture(0 + backend)
            if self.cap.isOpened():
                logging.info(f"Cámara abierta con backend: {backend}")
                break
        
        if not self.cap.isOpened():
            error_msg = "Error: No se pudo abrir la cámara con ningún backend."
            self.error.emit(error_msg)
            logging.error(error_msg)
            self.running = False
            return

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
                time.sleep(1)
                continue
            
            retry_count = 0  

            self.frame_count += 1

            if self.frame_count % self.frame_skip == 0:
                try:
                    self.process_frame(frame)
                except Exception as e:
                    error_msg = f"Error durante el procesamiento del frame: {str(e)}"
                    self.error.emit(error_msg)
                    logging.error(error_msg)

            self.update_ui(frame)
            self.check_resources()

        self.cleanup()

    def process_frame(self, frame):
        results = self.model(frame, verbose=False)

        detection_made = False
        for r in results:
            boxes = r.boxes
            for box in boxes:
                conf = box.conf[0]
                cls = int(box.cls[0])

                if conf > 0.5:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    color = self.colors.get(cls, (255, 255, 255))
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    label = f'{self.model.names[cls]} {conf:.2f}'
                    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
                    detection_made = True

        current_time = time.time()
        if detection_made and (current_time - self.last_capture_time) >= self.capture_interval:
            self.saveDetection(frame)
            self.last_capture_time = current_time

    def update_ui(self, frame):
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        p = convert_to_qt_format.scaled(640, 480, Qt.KeepAspectRatio)
        self.changePixmap.emit(p)

    def check_resources(self):
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
                logging.debug(f"Recursos actualizados: CPU {cpu_percent:.1f}%, Memoria {memory_percent:.1f}%, GPU {gpu_info.get('gpu_load', 'N/A')}")
            except Exception as e:
                error_msg = f"Error al monitorear recursos: {str(e)}"
                self.error.emit(error_msg)
                logging.error(error_msg)
            
            self.last_resource_check = current_time

    def saveDetection(self, frame):
        try:
            save_path = self.resource_path("savedFrame")
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            cv2.imwrite(os.path.join(save_path, "frame.jpg"), frame)
            logging.info('Frame Guardado')
            self.postDetection()
        except Exception as e:
            error_msg = f"Error al guardar la detección: {str(e)}"
            self.error.emit(error_msg)
            logging.error(error_msg)

    def postDetection(self):
        try:
            url = 'https://weapondetectionsystem.onrender.com/api/images/'
            headers = {'Authorization': 'Token ' + self.token}
            files = {'image': open(self.resource_path('savedFrame/frame.jpg'), 'rb')}
            data = {'userID': self.token, 'location': self.location, 'alertReceiver': self.receiver}
            
            response = requests.post(url, files=files, headers=headers, data=data, timeout=30)

            if response.ok:
                logging.info('Se ha enviado la alerta al servidor')
            else:
                error_msg = f'Error al enviar la alerta al servidor. Código de estado: {response.status_code}'
                self.error.emit(error_msg)
                logging.error(error_msg)
        except requests.exceptions.Timeout:
            error_msg = 'Tiempo de espera agotado al intentar conectar con el servidor'
            self.error.emit(error_msg)
            logging.error(error_msg)
        except requests.exceptions.ConnectionError:
            error_msg = 'Error de conexión al intentar conectar con el servidor'
            self.error.emit(error_msg)
            logging.error(error_msg)
        except Exception as e:
            error_msg = f'Error al acceder al servidor: {str(e)}'
            self.error.emit(error_msg)
            logging.error(error_msg)

    def cleanup(self):
        if self.cap:
            self.cap.release()
        logging.info("Hilo de detección terminado.")

    def stop(self):
        self.running = False
        logging.info("Deteniendo el hilo de detección")

    def resource_path(self, relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)