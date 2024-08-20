from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QImage
import cv2
import time
from ultralytics import YOLO
import numpy as np
import psutil
import GPUtil
import requests
import traceback

class Detection(QThread):
    changePixmap = pyqtSignal(QImage)
    resourceUpdate = pyqtSignal(dict)  

    def __init__(self, model_path, token, location, receiver):
        super(Detection, self).__init__()
        self.model_path = model_path
        self.colors = {0: (0, 0, 255), 1: (0, 165, 255)}  
        self.last_resource_check = 0
        self.resource_check_interval = 1  
        self.token = token
        self.location = location
        self.receiver = receiver
        self.last_capture_time = 0
        self.capture_interval = 2  # Intervalo de captura en segundos
        self.frame_skip = 1  # Procesar 1 frame cada 10 frames
        self.frame_count = 0

    def monitor_resources(self):
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
        except:
            pass  

        resources = {
            'cpu': cpu_percent,
            'memory': memory_percent,
            **gpu_info
        }
        
        self.resourceUpdate.emit(resources)

    def run(self):
        self.running = True
        
        model = YOLO(self.model_path)
        print("Clases disponibles:", model.names)

        cap = cv2.VideoCapture(0)

        while self.running:
            ret, frame = cap.read()
            self.frame_count += 1

            if ret:
                if self.frame_count % self.frame_skip == 0:
                    results = model(frame, verbose=False)  # Desactivar la salida verbose

                    detection_made = False
                    for r in results:
                        boxes = r.boxes
                        for box in boxes:
                            conf = box.conf[0]
                            cls = int(box.cls[0])

                            if conf > 0.5:
                                x1, y1, x2, y2 = box.xyxy[0]
                                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                                color = self.colors.get(cls, (255, 255, 255))
                                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                                label = f'{model.names[cls]} {conf:.2f}'
                                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
                                detection_made = True
        
                    current_time = time.time()
                    if detection_made and (current_time - self.last_capture_time) >= self.capture_interval:
                        self.saveDetection(frame)
                        self.last_capture_time = current_time

                rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgbImage.shape
                bytesPerLine = ch * w
                convertToQtFormat = QImage(rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888)
                p = convertToQtFormat.scaled(854, 480, Qt.KeepAspectRatio)
                self.changePixmap.emit(p)

                # Monitorear recursos
                current_time = time.time()
                if current_time - self.last_resource_check >= self.resource_check_interval:
                    self.monitor_resources()
                    self.last_resource_check = current_time

        cap.release()

    def saveDetection(self, frame):
        cv2.imwrite("savedFrame/frame.jpg", frame)
        print('Frame Saved')
        self.postDetection()

    def postDetection(self):
        try:
            url = 'http://127.0.0.1:8000/api/images/'
            headers = {'Authorization': 'Token ' + self.token}
            files = {'image': open('savedFrame/frame.jpg', 'rb')}
            data = {'userID': self.token, 'location': self.location, 'alertReceiver': self.receiver}
            response = requests.post(url, files=files, headers=headers, data=data)

            if response.ok:
                print('Alert was sent to the server')
            else:
                print('Unable to send alert to the server')
        except Exception as e:
            print(f'Error al acceder al servidor: {str(e)}')
            print(traceback.format_exc())