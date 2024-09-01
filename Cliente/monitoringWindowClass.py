from PyQt5.QtWidgets import QMainWindow, QMessageBox, QPushButton
from PyQt5.QtCore import pyqtSignal
from PyQt5.uic import loadUi
import os
import sys

class MonitoringWindow(QMainWindow):
    startMonitoringSignal = pyqtSignal(str, str, str)
    logoutSignal = pyqtSignal()

    def __init__(self, token):
        super(MonitoringWindow, self).__init__()
        ui_file = self.resource_path('UI/monitoringWindow.ui')
        loadUi(ui_file, self)
        self.token = token
        
        # Verificar y conectar el botón de inicio de monitoreo
        if hasattr(self, 'startMonitoring'):
            self.startMonitoring.clicked.connect(self.goToMonitoringPage)
        else:
            print("Advertencia: No se encontró el botón 'startMonitoring' en la interfaz de usuario.")

        # Verificar y conectar el botón de cierre de sesión
        if hasattr(self, 'logoutButton'):
            self.logoutButton.clicked.connect(self.logout)
        else:
            print("Advertencia: No se encontró el botón 'logoutButton' en la interfaz de usuario.")
            # Crear un botón de cierre de sesión si no existe

        self.setWindowTitle("Monitoring - Weapon Detection")

    def goToMonitoringPage(self):
        if hasattr(self, 'ubicationInput') and hasattr(self, 'receiveInput'):
            if self.ubicationInput.text() == '' or self.receiveInput.text() == '':
                self.showErrorMessage("Campos vacíos", "Los campos no deben estar vacíos.")
            else:
                self.startMonitoringSignal.emit(self.token, self.ubicationInput.text(), self.receiveInput.text())
        else:
            self.showErrorMessage("Error de UI", "No se encontraron los campos de ubicación o receptor en la interfaz de usuario.")

    def logout(self):
        self.logoutSignal.emit()

    def showErrorMessage(self, title, message):
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Warning)
        error_box.setWindowTitle(title)
        error_box.setText(message)
        error_box.exec_()

    def resource_path(self, relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)