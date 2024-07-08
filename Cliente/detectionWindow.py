from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.uic import loadUi
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QImage, QPixmap
from detection import Detection


class DetectionWindow(QMainWindow):
    def __init__(self):
        super(DetectionWindow,self).__init__()
        loadUi('UI/monitoringCameraWindow.ui',self)
        self.stopButton.clicked.connect(self.close)

    def createDetectionInstance(self):
        self.detection= Detection()

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
     
