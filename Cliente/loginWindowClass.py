from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtCore import pyqtSignal
from PyQt5.uic import loadUi
import requests
import json
import os
import sys
import traceback
import webbrowser

class LoginWindow(QMainWindow):
    loginSuccessful = pyqtSignal(str)

    def __init__(self):
        super(LoginWindow, self).__init__()
        ui_file = self.resource_path('UI/loginWindow.ui')
        loadUi(ui_file, self)
        self.registerButton.clicked.connect(self.goToRegisterPage)
        self.loginButton.clicked.connect(self.login)
        self.setWindowTitle("Login - Weapon Detection")

    def login(self):
        username = self.usernameInput.text()
        password = self.passwordInput.text()

        if not username or not password:
            self.showErrorMessage("Campos vacíos", "Por favor, ingrese tanto el nombre de usuario como la contraseña.")
            return

        try:
            url = 'http://127.0.0.1:8000/api/get_auth_token/'
            response = requests.post(url, data={'username': username, 'password': password}, timeout=10)
            
            print(f"Código de estado de la respuesta: {response.status_code}")
            print(f"Contenido de la respuesta: {response.text}")

            if response.ok:
                try:
                    json_response = response.json()
                    if 'token' in json_response:
                        self.loginSuccessful.emit(json_response['token'])
                        self.close()  # Cerrar la ventana de inicio de sesión después de un inicio de sesión exitoso
                        print("Inicio de sesión exitoso. Token recibido.")
                    else:
                        self.showErrorMessage("Error de inicio de sesión", "La respuesta del servidor no contiene un token.")
                except json.JSONDecodeError:
                    self.showErrorMessage("Error de respuesta", "No se pudo decodificar la respuesta del servidor.")
            else:
                error_message = f"Error de inicio de sesión. Código de estado: {response.status_code}"
                if response.text:
                    error_message += f"\nRespuesta del servidor: {response.text}"
                self.showErrorMessage("Error de inicio de sesión", error_message)

        except requests.exceptions.Timeout:
            self.showErrorMessage("Tiempo de espera agotado", "El servidor no respondió a tiempo. Por favor, inténtelo de nuevo más tarde.")
        except requests.exceptions.ConnectionError:
            self.showErrorMessage("Error de conexión", "No se pudo conectar al servidor. Verifique su conexión a internet y que el servidor esté en funcionamiento.")
        except Exception as e:
            error_message = f"Ocurrió un error inesperado: {str(e)}\n\n"
            error_message += traceback.format_exc()
            self.showErrorMessage("Error inesperado", error_message)
            print(error_message)  # Imprimir el error en la consola para depuración

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

    def goToRegisterPage(self):
        try:
            webbrowser.open('http://127.0.0.1:8000/register/')
            print("Página de registro abierta en el navegador.")
        except Exception as e:
            error_message = f"No se pudo abrir la página de registro: {str(e)}"
            self.showErrorMessage("Error al abrir la página de registro", error_message)
            print(error_message)  # Imprimir el error en la consola para depuración