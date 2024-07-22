from PyQt5.QtWidgets import QMainWindow, QLabel
from PyQt5.uic import loadUi
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QImage, QPixmap
from detection import Detection


class DetectionWindow(QMainWindow):
    def __init__(self):
        super(DetectionWindow, self).__init__()
        loadUi('UI/monitoringCameraWindow.ui', self)
        self.model_path = "model/predict.pt"  
        self.detection = None
        self.stopButton.clicked.connect(self.close)
        self.cpuLabel = getattr(self, 'cpuLabel', QLabel("CPU: 0%", self))
        self.memoryLabel = getattr(self, 'memoryLabel', QLabel("Memoria: 0%", self))
        self.gpuLabel = getattr(self, 'gpuLabel', QLabel("GPU: 0%", self))

        [label.move(10, y) for label, y in zip(
        [self.cpuLabel, self.memoryLabel, self.gpuLabel],
        [10, 40, 70]
        )]

    def createDetectionInstance(self,token,location,receiver):
        if self.detection is None:
            self.detection = Detection(self.model_path, token,location, receiver)
            self.detection.resourceUpdate.connect(self.updateResourceInfo)

    def updateResourceInfo(self, resources):
        getattr(self, 'cpuLabel', None) and self.cpuLabel.setText(f"CPU: {resources['cpu']:.1f}%")
        getattr(self, 'memoryLabel', None) and self.memoryLabel.setText(f"Memoria: {resources['memory']:.1f}%")
        'gpu_load' in resources and getattr(self, 'gpuLabel', None) and self.gpuLabel.setText(f"GPU: {resources['gpu_load']:.1f}%")

    @pyqtSlot(QImage)
    def setImage(self, image):
        self.CameraLabel.setPixmap(QPixmap.fromImage(image))
        
    def startDetection(self):
        if self.detection:
            self.detection.changePixmap.connect(self.setImage)
            self.detection.start()
        self.show()

    def closeEvent(self, event):
        if self.detection:
            self.detection.running = False
        event.accept()