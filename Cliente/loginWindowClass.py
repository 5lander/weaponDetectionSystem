from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.uic import loadUi
import webbrowser
import requests
import json
from monitoringWindowClass import MonitoringWindow

class LoginWindow(QMainWindow):
	def __init__(self):
		super(LoginWindow, self).__init__()
		loadUi('UI/loginWindow.ui',self)
		self.registerButton.clicked.connect(self.goToRegisterPage)
		self.loginButton.clicked.connect(self.login)
		self.popup = QMessageBox()
		self.popup.setWindowTitle("Fallo")

		self.show()


	def goToRegisterPage(self):
		webbrowser.open('http://127.0.0.1:8000/register/')


	def login(self):
		try:
			url = 'http://127.0.0.1:8000/api/get_auth_token/'
			response = requests.post(url, data={'username': self.usernameInput.text(),'password': self.passwordInput.text()})
			json_response = json.loads(response.text)


			if response.ok:

				self.openMonitoringWindow(json_response['token'])

			else:

				self.popup.setText("El usuario o la contrasena no estan correctos")
				self.popup.exec_()
		except:

			self.popup.setText("No se puede acceder al servidor")
			self.popup.exec_()
	

	def openMonitoringWindow(self, token):
		self.monitoringWindow = MonitoringWindow(token)
		self.monitoringWindow.displayInfo()
		self.close()
