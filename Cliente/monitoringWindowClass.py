from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.uic import loadUi
from detectionWindow import DetectionWindow

class MonitoringWindow(QMainWindow):
    def __init__(self, token):
        super(MonitoringWindow, self).__init__()
        loadUi('UI/monitoringWindow.ui', self)
        self.token = token


        self.detectionWindow =DetectionWindow()
        self.startMonitoring.clicked.connect(self.goToMonitoringPage)
        self.popup = QMessageBox()
        self.popup.setWindowTitle("Failed")
        self.popup.setText("Los campso no deben estar vacios.")

    def displayInfo(self):
        self.show()

    def goToMonitoringPage(self):
        if self.ubicationInput.text() == '' or self.startMonitoring.text() == '':
              self.popup.exec_()
        else:
            if self.detectionWindow.isVisible():
                print('La deteccion esta abierta')
            else:
                self.detectionWindow.createDetectionInstance(self.token, self.ubicationInput.text(), self.receiveInput.text())
                self.detectionWindow.startDetection()

    def closeEvent(self,event):

        if self.detectionWindow.isVisible():
            self.detectionWindow.detection.running =False
            self.detectionWindow.close()
            event.accept()