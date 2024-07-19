from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.uic import loadUi
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QImage, QPixmap
from detection import Detection


class DetectionWindow(QMainWindow):
    def __init__(self):
        super(DetectionWindow,self).__init__()
        loadUi('UI/monitoringCameraWindow.ui',self)
        self.model_path = "model/predict.pt"  
        self.stopButton.clicked.connect(self.close)
        self.detection= None

    def createDetectionInstance(self):
        if self.detection is None:
            self.detection = Detection(self.model_path)

    @pyqtSlot(QImage)
    def  setImage(self,image):
        self.CameraLabel.setPixmap(QPixmap.fromImage(image))
        
    def startDetection(self):
        self.detection.changePixmap.connect(self.setImage)
        self.detection.start()
        self.show()


    def closeEvent(self,event):
        self.detection.running= False
        event.accept()
     
