from PyQt5.QtWidgets import QMainWindow, QLabel
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.uic import loadUi
from detection import Detection
import os
import sys
import logging

class DetectionWindow(QMainWindow):
    closed = pyqtSignal()

    def __init__(self, token, location, receiver):
        super(DetectionWindow, self).__init__()
        ui_file = self.resource_path('UI/monitoringCameraWindow.ui')
        loadUi(ui_file, self)
        self.token = token
        self.location = location
        self.receiver = receiver
        self.model_path = self.resource_path("model/predict.pt")
        self.detection = None
        self.stopButton.clicked.connect(self.close_detection)
        self.cpuLabel = getattr(self, 'cpuLabel', QLabel("CPU: 0%", self))
        self.memoryLabel = getattr(self, 'memoryLabel', QLabel("Memoria: 0%", self))
        self.gpuLabel = getattr(self, 'gpuLabel', QLabel("GPU: 0%", self))

        [label.move(10, y) for label, y in zip(
            [self.cpuLabel, self.memoryLabel, self.gpuLabel],
            [10, 40, 70]
        )]

        self.createDetectionInstance()
        logging.info("DetectionWindow inicializada")

    def createDetectionInstance(self):
        if self.detection is None:
            self.detection = Detection(self.model_path, self.token, self.location, self.receiver)
            self.detection.changePixmap.connect(self.setImage)
            self.detection.resourceUpdate.connect(self.updateResourceInfo)
            self.detection.error.connect(self.handleDetectionError)
            self.detection.start()
            logging.info("Instancia de Detection creada y iniciada")

    @pyqtSlot(QImage)
    def setImage(self, image):
        self.CameraLabel.setPixmap(QPixmap.fromImage(image))

    def updateResourceInfo(self, resources):
        self.cpuLabel.setText(f"CPU: {resources['cpu']:.1f}%")
        self.memoryLabel.setText(f"Memoria: {resources['memory']:.1f}%")
        if 'gpu_load' in resources:
            self.gpuLabel.setText(f"GPU: {resources['gpu_load']:.1f}%")

    def handleDetectionError(self, error_message):
        logging.error(f"Error en la detección: {error_message}")

    def closeEvent(self, event):
        logging.info("Cerrando DetectionWindow")
        self.close_detection()
        self.closed.emit()
        super().closeEvent(event)

    def close_detection(self):
        if self.detection:
            self.detection.stop()
            self.detection.wait()
            logging.info("Detección detenida")

    def resource_path(self, relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)