from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.uic import loadUi
from detectionWindow import DetectionWindow

class MonitoringWindow(QMainWindow):
    def __init__(self):
        super(MonitoringWindow, self).__init__()
        loadUi('UI/monitoringWindow.ui', self)

        self.startMonitoring.clicked.connect(self.goToMonitoringPage)
        self.detectionWindow =DetectionWindow()

    def displayInfo(self):
        self.show()

    def goToMonitoringPage(self):
        if self.detectionWindow.isVisible():
            print('La deteccion esta abierta')
        else:
            self.detectionWindow.createDetectionInstance()
            self.detectionWindow.startDetection()

    def closeEvent(self,event):

        if self.detectionWindow.isVisible():
            self.detectionWindow.detection.running =False
            self.detectionwindow.close()
            event.accept()