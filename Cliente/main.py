import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, QSharedMemory
from loginWindowClass import LoginWindow
from monitoringWindowClass import MonitoringWindow
from detectionWindow import DetectionWindow

def setup_logging():
    try:
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))
        
        log_file = os.path.join(application_path, 'app_log.log')
        logging.basicConfig(filename=log_file, level=logging.DEBUG, 
                            format='%(asctime)s - %(levelname)s - %(message)s')
        logging.info(f"Logging iniciado. Archivo de log: {log_file}")
    except Exception as e:
        print(f"Error al configurar logging: {e}")
        logging.basicConfig(level=logging.DEBUG, 
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            handlers=[logging.StreamHandler()])
        logging.error(f"No se pudo configurar el archivo de log. Usando consola. Error: {e}")

class MainApplication(QObject):
    def __init__(self):
        super().__init__()
        setup_logging()
        self.app = QApplication(sys.argv)
        self.current_window = None
        self.is_logged_in = False
        self.current_token = None

    def start(self):
        logging.debug("Iniciando la aplicación")
        self.show_login()
        return self.app.exec_()

    def show_login(self):
        if not self.is_logged_in:
            logging.debug("Creando y mostrando ventana de login")
            self.close_current_window()
            self.current_window = LoginWindow()
            self.current_window.loginSuccessful.connect(self.on_login_successful)
            self.current_window.show()
            logging.info("Ventana de login abierta")
        else:
            logging.debug("Usuario ya está logueado, no se muestra ventana de login")

    def on_login_successful(self, token):
        logging.debug(f"Login exitoso. Token: {token}")
        self.is_logged_in = True
        self.current_token = token
        self.show_monitoring(token)

    def show_monitoring(self, token):
        logging.debug(f"Mostrando ventana de monitoreo. Token: {token}")
        self.close_current_window()
        self.current_window = MonitoringWindow(token)
        self.current_window.startMonitoringSignal.connect(self.show_detection)
        self.current_window.logoutSignal.connect(self.logout)
        self.current_window.show()
        logging.info("Ventana de monitoreo abierta")

    def show_detection(self, token, location, receiver):
        logging.debug(f"Mostrando ventana de detección. Token: {token}, Location: {location}, Receiver: {receiver}")
        self.close_current_window()
        self.current_window = DetectionWindow(token, location, receiver)
        self.current_window.closed.connect(self.on_detection_closed)
        self.current_window.show()
        logging.info("Ventana de detección abierta")

    def on_detection_closed(self):
        logging.debug("Ventana de detección cerrada")
        self.show_monitoring(self.current_token)

    def logout(self):
        logging.debug("Cerrando sesión")
        self.is_logged_in = False
        self.current_token = None
        self.close_current_window()
        self.show_login()

    def close_current_window(self):
        if self.current_window:
            logging.debug(f"Cerrando ventana actual: {type(self.current_window).__name__}")
            self.current_window.close()
            self.current_window.deleteLater()
            self.current_window = None

if __name__ == '__main__':
    shared_memory = QSharedMemory("WeaponDetectionApp")
    if shared_memory.attach():
        print("Application is already running")
        logging.warning("Se intentó iniciar una segunda instancia de la aplicación")
        sys.exit()
    
    shared_memory.create(1)
    try:
        main_app = MainApplication()
        sys.exit(main_app.start())
    except Exception as e:
        logging.exception(f"Error no manejado en la aplicación principal: {e}")
        raise
    finally:
        shared_memory.detach()