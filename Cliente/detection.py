from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QImage
import cv2
import time
from ultralytics import YOLO
import numpy as np

class Detection(QThread):
    changePixmap = pyqtSignal(QImage)

    def __init__(self, model_path):
        super(Detection, self).__init__()
        self.model_path = model_path

    def run(self):
        self.running = True
        
        # Cargar el modelo YOLOv8
        model = YOLO("model/predict.pt")

        # Configurar la captura de video
        cap = cv2.VideoCapture(0)
        
        startingTime = time.time()

        while self.running:
            ret, frame = cap.read()

            if ret:
                # Realizar la detección
                results = model(frame)

                # Procesar los resultados
                for r in results:
                    boxes = r.boxes
                    for box in boxes:
                        # Obtener las coordenadas del cuadro delimitador
                        x1, y1, x2, y2 = box.xyxy[0]
                        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                        
                        # Obtener la confianza y la clase
                        conf = box.conf[0]
                        cls = int(box.cls[0])

                        if conf > 0.5:  # Umbral de confianza
                            # Dibujar el cuadro delimitador
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            
                            # Añadir etiqueta
                            label = f'{model.names[cls]} {conf:.2f}'
                            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

                # Guardar el frame cada 10 segundos
                elapsedTime = time.time() - startingTime
                if elapsedTime >= 10:
                    startingTime = time.time()
                    self.saveDetection(frame)

                # Convertir el frame a QImage y emitir la señal
                rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgbImage.shape
                bytesPerLine = ch * w
                convertToQtFormat = QImage(rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888)
                p = convertToQtFormat.scaled(854, 480, Qt.KeepAspectRatio)
                self.changePixmap.emit(p)

        cap.release()

    def saveDetection(self, frame):
        cv2.imwrite("savedFrame/frame.jpg", frame)
        print("Frame Guardado")