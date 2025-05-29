from PyQt5.QtWidgets import QMainWindow, QMessageBox, QLabel, QProgressBar, QFrame, QWidget
from PyQt5.QtCore import pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, Qt
from PyQt5.QtGui import QFont, QIcon
from PyQt5.uic import loadUi
import requests
import json
import os
import sys
import traceback
import webbrowser
import logging

# Importar los estilos desde la carpeta Styles
from Styles.loginStyle import LoginWindowStyles, StatusIndicatorStyles

class StatusIndicator(QLabel):
    """Indicador de estado de conexión moderno"""
    def __init__(self):
        super().__init__()
        self.setFixedSize(12, 12)
        self.status = "checking"
        self.set_status("checking")
        
    def set_status(self, status):
        """Establece el estado y aplica el estilo correspondiente"""
        self.status = status
        style = StatusIndicatorStyles.get_status_style(status)
        self.setStyleSheet(style)

class LoginWindow(QMainWindow):
    loginSuccessful = pyqtSignal(str)

    def __init__(self):
        super(LoginWindow, self).__init__()
        
        # Definir resource_path ANTES de usarlo
        self.setup_resource_path()
        
        # Cargar UI original
        ui_file = self.resource_path('UI/loginWindow.ui')
        
        # Verificar si el archivo UI existe
        if not os.path.exists(ui_file):
            logging.error(f"Archivo UI no encontrado: {ui_file}")
            self.create_ui_programmatically()
        else:
            loadUi(ui_file, self)
        
        # ARREGLAR LAS DIMENSIONES Y POSICIONAMIENTO
        self.fix_component_positioning()
        
        # Aplicar mejoras visuales
        self.setup_modern_enhancements()
        
        # Mejorar la barra de título
        self.customize_title_bar()
        
        # Mantener conexiones originales
        self.registerButton.clicked.connect(self.goToRegisterPage)
        self.loginButton.clicked.connect(self.login)
        self.setWindowTitle("Login - Weapon Detection")
        
        logging.info("Ventana de login inicializada")

    def setup_resource_path(self):
        """Configura el método resource_path"""
        if hasattr(sys, '_MEIPASS'):
            self.base_path = sys._MEIPASS
        else:
            self.base_path = os.path.abspath(".")
    
    def resource_path(self, relative_path):
        """Obtiene la ruta completa del recurso"""
        return os.path.join(self.base_path, relative_path)

    def create_ui_programmatically(self):
        """Crea la UI programáticamente si no existe el archivo .ui"""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Configurar ventana
        self.setFixedSize(400, 450)
        self.setMinimumSize(400, 450)
        self.setMaximumSize(400, 450)
        
        # Crear componentes
        self.labelTitle = QLabel("Weapon Detection", central_widget)
        self.labelTitle.setGeometry(30, 65, 340, 45)
        self.labelTitle.setAlignment(Qt.AlignCenter)
        
        self.labelUsername = QLabel("Username:", central_widget)
        self.labelPassword = QLabel("Password:", central_widget)
        
        from PyQt5.QtWidgets import QLineEdit, QPushButton
        
        self.usernameInput = QLineEdit(central_widget)
        self.usernameInput.setPlaceholderText("Enter your username")
        
        self.passwordInput = QLineEdit(central_widget)
        self.passwordInput.setPlaceholderText("Enter your password")
        self.passwordInput.setEchoMode(QLineEdit.Password)
        
        self.loginButton = QPushButton("Login", central_widget)
        self.registerButton = QPushButton("Register", central_widget)
        
        # Configurar fuentes
        font = QFont("Segoe UI")
        self.setFont(font)
        
        title_font = QFont("Segoe UI", 18, QFont.Bold)
        self.labelTitle.setFont(title_font)

    def customize_title_bar(self):
        """Personaliza la barra de título de la ventana"""
        try:
            icon_path = self.resource_path('UI/icon.ico')
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except:
            pass

    def fix_component_positioning(self):
        """Arregla el posicionamiento y dimensiones de los componentes"""
        # Hacer la ventana un poco más grande para mejor distribución
        self.setFixedSize(400, 450)
        
        # Reposicionar título
        self.labelTitle.setGeometry(30, 65, 340, 45)
        self.labelTitle.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.labelTitle.setAlignment(Qt.AlignCenter)
        
        # Reposicionar labels y inputs con mejor espaciado
        self.labelUsername.setGeometry(60, 120, 100, 25)
        self.usernameInput.setGeometry(60, 150, 280, 40)
        
        self.labelPassword.setGeometry(60, 210, 100, 25)  
        self.passwordInput.setGeometry(60, 240, 280, 40)
        
        # Reposicionar botones con mejor espaciado
        self.loginButton.setGeometry(60, 320, 120, 45)
        self.registerButton.setGeometry(200, 320, 120, 45)

    def setup_modern_enhancements(self):
        """Aplica mejoras modernas manteniendo la funcionalidad original"""
        self.apply_modern_styling()
        self.add_status_indicator()
        self.add_progress_indicator() 
        self.setup_animations()
        self.enhance_form_validation()
        
    def apply_modern_styling(self):
        """Aplica estilos modernos usando los estilos separados"""
        # Aplicar estilos desde el archivo de estilos
        self.setStyleSheet(LoginWindowStyles.MAIN_WINDOW)
        self.labelTitle.setStyleSheet(LoginWindowStyles.TITLE_LABEL)
        self.usernameInput.setStyleSheet(LoginWindowStyles.INPUT_FIELD)
        self.passwordInput.setStyleSheet(LoginWindowStyles.INPUT_FIELD)
        self.loginButton.setStyleSheet(LoginWindowStyles.LOGIN_BUTTON)
        self.registerButton.setStyleSheet(LoginWindowStyles.REGISTER_BUTTON)
        self.labelUsername.setStyleSheet(LoginWindowStyles.LABEL_STYLE)
        self.labelPassword.setStyleSheet(LoginWindowStyles.LABEL_STYLE)

    def add_status_indicator(self):
        """Añade indicador de estado de conexión bien posicionado"""
        # Crear frame para el indicador de estado
        self.status_frame = QFrame(self)
        self.status_frame.setGeometry(20, 15, 180, 35)
        self.status_frame.setStyleSheet(LoginWindowStyles.STATUS_FRAME)
        
        # Indicador visual
        self.status_indicator = StatusIndicator()
        self.status_indicator.setParent(self.status_frame)
        self.status_indicator.move(12, 11)
        
        # Texto de estado
        self.status_label = QLabel("Checking connection...", self.status_frame)
        self.status_label.setGeometry(32, 7, 140, 21)
        self.status_label.setStyleSheet(LoginWindowStyles.STATUS_LABEL)
        
        # Iniciar verificación de estado
        self.check_server_status()
        
    def add_progress_indicator(self):
        """Añade barra de progreso bien posicionada"""
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(60, 380, 280, 8)
        self.progress_bar.setStyleSheet(LoginWindowStyles.PROGRESS_BAR)
        self.progress_bar.setVisible(False)
        
    def setup_animations(self):
        """Configura animaciones suaves"""
        # Animación de entrada de la ventana
        self.setWindowOpacity(0)
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(500)
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(1)
        self.fade_animation.setEasingCurve(QEasingCurve.OutQuart)
        self.fade_animation.start()
        
    def enhance_form_validation(self):
        """Mejora la validación de formularios en tiempo real"""
        # Conectar eventos de cambio de texto para validación
        self.usernameInput.textChanged.connect(self.validate_form)
        self.passwordInput.textChanged.connect(self.validate_form)
        
        # Validación inicial
        self.validate_form()
        
    def validate_form(self):
        """Valida el formulario en tiempo real"""
        username = self.usernameInput.text().strip()
        password = self.passwordInput.text().strip()
        
        # Habilitar/deshabilitar botón según validación
        is_valid = len(username) >= 3 and len(password) >= 6
        self.loginButton.setEnabled(is_valid)
        
        # Cambiar estilo de campos según validación
        if username and len(username) < 3:
            self.usernameInput.setStyleSheet(LoginWindowStyles.INPUT_FIELD_ERROR)
        elif password and len(password) < 6:
            self.passwordInput.setStyleSheet(LoginWindowStyles.INPUT_FIELD_ERROR)
        else:
            # Restaurar estilos normales
            self.apply_modern_styling()
            
    def check_server_status(self):
        """Verifica el estado del servidor"""
        self.status_indicator.set_status("checking")
        self.status_label.setText("Checking server...")
        
        try:
            response = requests.get('https://weapondetectionsystem.onrender.com/', timeout=5)
            if response.status_code == 200:
                self.status_indicator.set_status("connected")
                self.status_label.setText("Server online")
            else:
                self.status_indicator.set_status("error")
                self.status_label.setText("Server error")
        except:
            self.status_indicator.set_status("disconnected")
            self.status_label.setText("Server offline")

    def login(self):
        """Método de login original con mejoras visuales"""
        username = self.usernameInput.text()
        password = self.passwordInput.text()

        if not username or not password:
            self.showErrorMessage("Campos vacíos", "Por favor, ingrese tanto el nombre de usuario como la contraseña.")
            return

        # Añadir indicadores visuales de progreso
        self.start_login_animation()

        try:
            url = 'https://weapondetectionsystem.onrender.com/api/get_auth_token/'
            response = requests.post(url, data={'username': username, 'password': password}, timeout=10)
            
            logging.debug(f"Código de estado de la respuesta: {response.status_code}")
            logging.debug(f"Contenido de la respuesta: {response.text}")

            if response.ok:
                try:
                    json_response = response.json()
                    if 'token' in json_response:
                        self.login_success_animation()
                        self.loginSuccessful.emit(json_response['token'])
                        self.close()
                        logging.info("Inicio de sesión exitoso. Token recibido.")
                    else:
                        self.stop_login_animation()
                        self.showErrorMessage("Error de inicio de sesión", "La respuesta del servidor no contiene un token.")
                except json.JSONDecodeError:
                    self.stop_login_animation()
                    self.showErrorMessage("Error de respuesta", "No se pudo decodificar la respuesta del servidor.")
            else:
                self.stop_login_animation()
                error_message = f"Error de inicio de sesión. Código de estado: {response.status_code}"
                if response.text:
                    error_message += f"\nRespuesta del servidor: {response.text}"
                self.showErrorMessage("Error de inicio de sesión", error_message)

        except requests.exceptions.Timeout:
            self.stop_login_animation()
            self.showErrorMessage("Tiempo de espera agotado", "El servidor no respondió a tiempo. Por favor, inténtelo de nuevo más tarde.")
        except requests.exceptions.ConnectionError:
            self.stop_login_animation() 
            self.status_indicator.set_status("error")
            self.status_label.setText("Connection failed")
            self.showErrorMessage("Error de conexión", "No se pudo conectar al servidor. Verifique su conexión a internet y que el servidor esté en funcionamiento.")
        except Exception as e:
            self.stop_login_animation()
            error_message = f"Ocurrió un error inesperado: {str(e)}\n\n"
            error_message += traceback.format_exc()
            self.showErrorMessage("Error inesperado", error_message)
            logging.error(error_message)

    def start_login_animation(self):
        """Inicia animación de login"""
        self.loginButton.setEnabled(False)
        self.loginButton.setText("Signing In...")
        
        # Mostrar y animar barra de progreso
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Simular progreso
        self.progress_timer = QTimer()
        self.progress_value = 0
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start(50)
        
    def update_progress(self):
        """Actualiza la barra de progreso"""
        self.progress_value += 3
        self.progress_bar.setValue(min(self.progress_value, 90))
        
    def login_success_animation(self):
        """Animación de éxito de login"""
        if hasattr(self, 'progress_timer'):
            self.progress_timer.stop()
        self.progress_bar.setValue(100)
        
        # Cambiar a estilo de éxito
        self.progress_bar.setStyleSheet(LoginWindowStyles.PROGRESS_BAR_SUCCESS)
        
    def stop_login_animation(self):
        """Detiene animación de login"""
        if hasattr(self, 'progress_timer'):
            self.progress_timer.stop()
            
        self.loginButton.setEnabled(True)
        self.loginButton.setText("Login")
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)

    def showErrorMessage(self, title, message):
        """Método de mostrar errores con mejoras visuales y responsive"""
        # Mejorar el mensaje para credenciales incorrectas
        if "400" in message or "inicio de sesión" in title.lower():
            title = "Credenciales Incorrectas"
            message = "El nombre de usuario o contraseña son incorrectos.\n\nPor favor, verifique sus datos e intente nuevamente."
        elif "conexión" in title.lower():
            title = "Error de Conexión"
            message = "No se pudo conectar al servidor.\n\nVerifique su conexión a internet e intente nuevamente."
        elif "tiempo" in message.lower():
            title = "Servidor No Disponible"
            message = "El servidor no está respondiendo en este momento.\n\nIntente nuevamente en unos minutos."
        
        error_box = QMessageBox(self)
        error_box.setIcon(QMessageBox.Warning)
        error_box.setWindowTitle(title)
        
        # HACER EL MENSAJE RESPONSIVE
        lines = message.split('\n')
        max_line_length = max(len(line) for line in lines) if lines else 0
        num_lines = len(lines)
        
        # Calcular dimensiones dinámicas
        char_width = 8
        line_height = 20
        min_width = 450
        max_width = 700
        
        calculated_width = max(min_width, min(max_width, max_line_length * char_width + 100))
        calculated_height = max(200, num_lines * line_height + 150)
        
        error_box.setText(title)
        error_box.setInformativeText(message)
        
        # Aplicar estilo usando el método del archivo de estilos
        style = LoginWindowStyles.get_message_box_style(calculated_width, calculated_height, max_width)
        error_box.setStyleSheet(style)
        
        error_box.exec_()
        logging.warning(f"Error mostrado al usuario: {title} - {message}")

    def goToRegisterPage(self):
        try:
            webbrowser.open('https://weapondetectionsystem.onrender.com/register/')
            print("Página de registro abierta en el navegador.")
        except Exception as e:
            error_message = f"No se pudo abrir la página de registro: {str(e)}"
            self.showErrorMessage("Error al abrir la página de registro", error_message)
            logging.error(error_message)

    def closeEvent(self, event):
        logging.info("Ventana de login cerrada")
        super().closeEvent(event)