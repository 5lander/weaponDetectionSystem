from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.uic import loadUi
from monitoringWindowClass import MonitoringWindow

class LoginWindow(QMainWindow):
    def __init__(self):
        super(LoginWindow,self).__init__()
        loadUi('UI/loginWindow.ui',self)

        self.registerButton.clicked.connect(self.goToRegisterPage)
        self.loginButton.clicked.connect(self.goToLoginPage)

        self.show()

    def goToRegisterPage(self):

        print("Ir a la pagina de registro ")

    def goToLoginPage(self):

        self.monitoringWindow = MonitoringWindow()
        self.monitoringWindow.displayInfo()
        self.close()
