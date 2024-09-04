from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.uic import loadUi
import os
import sys
import logging

class MonitoringWindow(QMainWindow):
    startMonitoringSignal = pyqtSignal(str, str, str)
    logoutSignal = pyqtSignal()

    def __init__(self, token):
        super(MonitoringWindow, self).__init__()
        ui_file = self.resource_path('UI/monitoringWindow.ui')
        loadUi(ui_file, self)
        self.token = token
        self.is_monitoring = False
        
        if hasattr(self, 'startMonitoring'):
            self.startMonitoring.clicked.connect(self.goToMonitoringPage)
        else:
            logging.warning("No se encontró el botón 'startMonitoring' en la interfaz de usuario.")

        if hasattr(self, 'logoutButton'):
            self.logoutButton.clicked.connect(self.logout)
        else:
            logging.warning("No se encontró el botón 'logoutButton' en la interfaz de usuario.")

        self.setWindowTitle("Monitoring - Weapon Detection")
        logging.info("MonitoringWindow inicializada")

    def goToMonitoringPage(self):
        if self.is_monitoring:
            logging.info("Monitoreo ya en progreso. Ignorando clic adicional.")
            return

        if hasattr(self, 'ubicationInput') and hasattr(self, 'receiveInput'):
            if self.ubicationInput.text() == '' or self.receiveInput.text() == '':
                self.showErrorMessage("Campos vacíos", "Los campos no deben estar vacíos.")
            else:
                logging.info(f"Iniciando monitoreo: Ubicación: {self.ubicationInput.text()}, Receptor: {self.receiveInput.text()}")
                self.is_monitoring = True
                self.startMonitoringSignal.emit(self.token, self.ubicationInput.text(), self.receiveInput.text())
        else:
            logging.error("No se encontraron los campos de ubicación o receptor en la interfaz de usuario.")
            self.showErrorMessage("Error de UI", "No se encontraron los campos de ubicación o receptor en la interfaz de usuario.")

    def stopMonitoring(self):
        self.is_monitoring = False
        logging.info("Monitoreo detenido")

    def logout(self):
        logging.info("Usuario cerrando sesión")
        self.is_monitoring = False
        self.logoutSignal.emit()

    def showErrorMessage(self, title, message):
        logging.warning(f"Mostrando mensaje de error: {title} - {message}")
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Warning)
        error_box.setWindowTitle(title)
        error_box.setText(message)
        error_box.exec_()

    def resource_path(self, relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

    def closeEvent(self, event):
        logging.info("Ventana de monitoreo cerrada")
        super().closeEvent(event)