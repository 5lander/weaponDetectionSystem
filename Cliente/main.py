import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject
from loginWindowClass import LoginWindow
from monitoringWindowClass import MonitoringWindow
from detectionWindow import DetectionWindow

class MainApplication(QObject):
    def __init__(self):
        super().__init__()
        self.app = QApplication(sys.argv)
        self.login_window = None
        self.monitoring_window = None
        self.detection_window = None
        self.is_logged_in = False
        self.current_token = None

    def start(self):
        self.show_login()
        return self.app.exec_()

    def show_login(self):
        if not self.is_logged_in:
            if self.login_window is None:
                self.login_window = LoginWindow()
                self.login_window.loginSuccessful.connect(self.on_login_successful)
            self.login_window.show()
        elif self.monitoring_window:
            self.monitoring_window.show()

    def on_login_successful(self, token):
        self.is_logged_in = True
        self.current_token = token
        if self.login_window:
            self.login_window.hide()
        self.show_monitoring(token)

    def show_monitoring(self, token):
        if self.monitoring_window is None:
            self.monitoring_window = MonitoringWindow(token)
            self.monitoring_window.startMonitoringSignal.connect(self.show_detection)
            self.monitoring_window.logoutSignal.connect(self.logout)
        self.monitoring_window.show()

    def show_detection(self, token, location, receiver):
        if self.monitoring_window:
            self.monitoring_window.hide()
        if self.detection_window is None:
            self.detection_window = DetectionWindow(token, location, receiver)
            self.detection_window.closed.connect(self.on_detection_closed)
        self.detection_window.show()

    def on_detection_closed(self):
        if self.detection_window:
            self.detection_window.hide()
            self.detection_window.deleteLater()
            self.detection_window = None
        if self.monitoring_window:
            self.monitoring_window.show()

    def logout(self):
        self.is_logged_in = False
        self.current_token = None
        if self.monitoring_window:
            self.monitoring_window.hide()
            self.monitoring_window.deleteLater()
            self.monitoring_window = None
        if self.detection_window:
            self.detection_window.close()
            self.detection_window.deleteLater()
            self.detection_window = None
        self.show_login()

if __name__ == '__main__':
    main_app = MainApplication()
    sys.exit(main_app.start())