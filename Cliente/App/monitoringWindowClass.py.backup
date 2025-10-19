# monitoringWindowClass.py - VERSIÓN CORREGIDA CON VALIDACIÓN DE EMAIL

from PyQt5.QtWidgets import QMainWindow, QMessageBox, QLabel, QProgressBar, QFrame, QWidget, QLineEdit, QPushButton
from PyQt5.QtCore import pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, Qt
from PyQt5.QtGui import QFont, QIcon
from PyQt5.uic import loadUi
import os
import sys
import logging
import re

# Importar los estilos desde la carpeta Styles
from Styles.monitoringStyle import MonitoringWindowStyles, MonitoringStatusIndicatorStyles

class MonitoringStatusIndicator(QLabel):
    """Indicador de estado de monitoreo moderno"""
    def __init__(self):
        super().__init__()
        self.setFixedSize(16, 16)
        self.status = "idle"
        self.set_status("idle")
        
    def set_status(self, status):
        """Establece el estado y aplica el estilo correspondiente"""
        self.status = status
        style = MonitoringStatusIndicatorStyles.get_status_style(status)
        self.setStyleSheet(style)

class MonitoringWindow(QMainWindow):
    startMonitoringSignal = pyqtSignal(str, str, str)
    logoutSignal = pyqtSignal()

    def __init__(self, token):
        super(MonitoringWindow, self).__init__()
        
        # Definir resource_path ANTES de usarlo
        self.setup_resource_path()
        
        # Cargar UI original
        ui_file = self.resource_path('UI/monitoringWindow.ui')
        
        # Verificar si el archivo UI existe
        if not os.path.exists(ui_file):
            logging.error(f"Archivo UI no encontrado: {ui_file}")
            self.create_ui_programmatically()
        else:
            loadUi(ui_file, self)
        
        self.token = token
        self.is_monitoring = False  # INICIALIZAR CORRECTAMENTE EN FALSE
        
        # MEJORAR LAS DIMENSIONES Y POSICIONAMIENTO - CORREGIDO
        self.fix_component_positioning()
        
        # Aplicar mejoras visuales
        self.setup_modern_enhancements()
        
        # Mejorar la barra de título
        self.customize_title_bar()
        
        # Conectar eventos originales
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
        """Crea la UI programáticamente si no existe el archivo .ui - DIMENSIONES CORREGIDAS"""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Configurar ventana
        self.setFixedSize(420, 480)
        
        # Crear componentes con ALTURA SUFICIENTE
        self.infoText = QLabel("Configure su sistema de monitoreo ingresando la ubicación de la cámara y un contacto para recibir notificaciones de alertas de seguridad.", central_widget)
        self.infoText.setGeometry(30, 30, 360, 110)
        self.infoText.setAlignment(Qt.AlignJustify | Qt.AlignVCenter)
        self.infoText.setWordWrap(True)
        
        self.ubicationLabel = QLabel("Ubicación de la Cámara:", central_widget)
        self.ubicationLabel.setGeometry(40, 160, 220, 25)
        
        self.receiveLabel = QLabel("Contacto para Notificaciones:", central_widget)
        self.receiveLabel.setGeometry(40, 260, 220, 25)
        
        # CAMPOS DE ENTRADA CON ALTURA CORREGIDA
        self.ubicationInput = QLineEdit(central_widget)
        self.ubicationInput.setGeometry(40, 190, 340, 45)  # Altura aumentada de 50 a 45
        self.ubicationInput.setPlaceholderText("Ej: Oficina Principal - Entrada Norte")
        
        self.receiveInput = QLineEdit(central_widget)
        self.receiveInput.setGeometry(40, 290, 340, 45)    # Altura aumentada de 50 a 45
        self.receiveInput.setPlaceholderText("Ej: correo@empresa.com o +593987654321")
        
        self.startMonitoring = QPushButton("▶ Iniciar Monitoreo", central_widget)
        self.startMonitoring.setGeometry(40, 355, 150, 55)  # Y ajustado
        
        self.logoutButton = QPushButton("✕ Cerrar Sesión", central_widget)
        self.logoutButton.setGeometry(210, 355, 150, 55)   # Y ajustado
        
        # Configurar fuentes
        font = QFont("Segoe UI")
        self.setFont(font)

    def customize_title_bar(self):
        """Personaliza la barra de título de la ventana"""
        try:
            icon_path = self.resource_path('UI/icon.ico')
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except:
            pass

    def fix_component_positioning(self):
        """Arregla el posicionamiento y dimensiones de los componentes - CORREGIDO"""
        # Hacer la ventana más grande para mejor distribución
        self.setFixedSize(420, 480)
        
        # Reposicionar y redimensionar componentes con mejor espaciado
        if hasattr(self, 'infoText'):
            self.infoText.setGeometry(30, 30, 360, 110)
            self.infoText.setAlignment(Qt.AlignJustify | Qt.AlignVCenter)
            self.infoText.setWordWrap(True)
        
        # Labels y inputs con mejor espaciado y ALTURA CORREGIDA
        if hasattr(self, 'ubicationLabel'):
            self.ubicationLabel.setGeometry(40, 160, 220, 25)
        if hasattr(self, 'ubicationInput'):
            self.ubicationInput.setGeometry(40, 190, 340, 45)  # Altura corregida
        
        if hasattr(self, 'receiveLabel'):
            self.receiveLabel.setGeometry(40, 260, 220, 25)
        if hasattr(self, 'receiveInput'):
            self.receiveInput.setGeometry(40, 290, 340, 45)   # Altura corregida
        
        # Botones con mejor espaciado y tamaño - Y ajustado por cambio de altura de inputs
        if hasattr(self, 'startMonitoring'):
            self.startMonitoring.setGeometry(40, 355, 150, 55)  # Y ajustado
        if hasattr(self, 'logoutButton'):
            self.logoutButton.setGeometry(210, 355, 150, 55)   # Y ajustado

    def setup_modern_enhancements(self):
        """Aplica mejoras modernas manteniendo la funcionalidad original"""
        self.apply_modern_styling()
        self.add_progress_indicator() 
        self.setup_animations()
        self.enhance_form_validation()
        self.add_placeholders()
        
    def apply_modern_styling(self):
        """Aplica estilos modernos usando los estilos separados"""
        # Aplicar estilos desde el archivo de estilos
        self.setStyleSheet(MonitoringWindowStyles.MAIN_WINDOW)
        self.infoText.setStyleSheet(MonitoringWindowStyles.INFO_TEXT)
        self.ubicationLabel.setStyleSheet(MonitoringWindowStyles.FIELD_LABEL)
        self.receiveLabel.setStyleSheet(MonitoringWindowStyles.FIELD_LABEL)
        self.ubicationInput.setStyleSheet(MonitoringWindowStyles.INPUT_FIELD)
        self.receiveInput.setStyleSheet(MonitoringWindowStyles.INPUT_FIELD)
        self.startMonitoring.setStyleSheet(MonitoringWindowStyles.MONITORING_BUTTON)
        self.logoutButton.setStyleSheet(MonitoringWindowStyles.LOGOUT_BUTTON)

    def add_placeholders(self):
        """Añade placeholders a los campos de entrada"""
        if hasattr(self, 'ubicationInput'):
            self.ubicationInput.setPlaceholderText("Ej: Oficina Principal - Entrada Norte")
        if hasattr(self, 'receiveInput'):
            self.receiveInput.setPlaceholderText("Ej: correo@empresa.com o +593987654321")

    def add_progress_indicator(self):
        """Añade barra de progreso bien posicionada - Y AJUSTADO"""
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(40, 425, 340, 12)  # Y ajustado por nueva posición de botones
        self.progress_bar.setStyleSheet(MonitoringWindowStyles.PROGRESS_BAR)
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
        self.ubicationInput.textChanged.connect(self.validate_form)
        self.receiveInput.textChanged.connect(self.validate_form)
        
        # Validación inicial
        self.validate_form()

    def is_valid_email(self, email):
        """Valida si el texto es un email válido"""
        # Patrón regex para validar email básico
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def is_valid_phone(self, phone):
        """Valida si el texto es un teléfono válido (formato básico)"""
        # Remover espacios y caracteres especiales comunes
        clean_phone = re.sub(r'[\s\-\(\)\+]', '', phone)
        # Verificar que tenga entre 7 y 15 dígitos
        return clean_phone.isdigit() and 7 <= len(clean_phone) <= 15

    def is_valid_contact(self, contact):
        """Valida si el contacto es un email o teléfono válido"""
        contact = contact.strip()
        if not contact:
            return False
        
        # Verificar si es email o teléfono
        if '@' in contact:
            return self.is_valid_email(contact)
        else:
            return self.is_valid_phone(contact)
        
    def validate_form(self):
        """Valida el formulario en tiempo real con validación de email"""
        ubicacion = self.ubicationInput.text().strip()
        contacto = self.receiveInput.text().strip()
        
        # Validar ubicación
        ubicacion_valid = len(ubicacion) >= 3
        
        # Validar contacto (email o teléfono)
        contacto_valid = self.is_valid_contact(contacto)
        
        # Habilitar/deshabilitar botón según validación
        is_valid = ubicacion_valid and contacto_valid
        self.startMonitoring.setEnabled(is_valid and not self.is_monitoring)
        
        # Cambiar estilo de campos según validación
        if ubicacion and not ubicacion_valid:
            self.ubicationInput.setStyleSheet(MonitoringWindowStyles.INPUT_FIELD_ERROR)
        else:
            self.ubicationInput.setStyleSheet(MonitoringWindowStyles.INPUT_FIELD)
            
        if contacto and not contacto_valid:
            self.receiveInput.setStyleSheet(MonitoringWindowStyles.INPUT_FIELD_ERROR)
        else:
            self.receiveInput.setStyleSheet(MonitoringWindowStyles.INPUT_FIELD)

    def goToMonitoringPage(self):
        """Método original mejorado con validación corregida"""
        # VERIFICAR ESTADO ACTUAL CORRECTAMENTE
        if self.is_monitoring:
            # Detener monitoreo
            self.stop_monitoring_animation()
            self.is_monitoring = False
            logging.info("Monitoreo detenido por el usuario.")
            return

        # VALIDAR CAMPOS ANTES DE CONTINUAR
        if hasattr(self, 'ubicationInput') and hasattr(self, 'receiveInput'):
            ubicacion = self.ubicationInput.text().strip()
            contacto = self.receiveInput.text().strip()
            
            # Verificar campos vacíos
            if not ubicacion or not contacto:
                self.showErrorMessage("Campos vacíos", "Todos los campos son obligatorios.")
                return
            
            # Validar ubicación
            if len(ubicacion) < 3:
                self.showErrorMessage("Ubicación inválida", "La ubicación debe tener al menos 3 caracteres.")
                return
            
            # Validar contacto
            if not self.is_valid_contact(contacto):
                if '@' in contacto:
                    self.showErrorMessage("Email inválido", "Por favor ingrese un email válido.\n\nEjemplo: usuario@gmail.com")
                else:
                    self.showErrorMessage("Contacto inválido", "Por favor ingrese un email válido o un número de teléfono.\n\nEjemplos:\n• usuario@gmail.com\n• +593987654321")
                return
            
            # Si llegamos aquí, todo está válido
            logging.info(f"Iniciando monitoreo: Ubicación: {ubicacion}, Receptor: {contacto}")
            self.start_monitoring_animation()
            self.is_monitoring = True
            self.startMonitoringSignal.emit(self.token, ubicacion, contacto)
        else:
            logging.error("No se encontraron los campos de ubicación o receptor en la interfaz de usuario.")
            self.showErrorMessage("Error de UI", "No se encontraron los campos de ubicación o receptor en la interfaz de usuario.")

    def start_monitoring_animation(self):
        """Inicia animación de monitoreo"""
        # Cambiar botón a modo detener
        self.startMonitoring.setText("⏹️ Detener Monitoreo")
        self.startMonitoring.setStyleSheet(MonitoringWindowStyles.MONITORING_BUTTON_ACTIVE)
        
        # Mostrar y animar barra de progreso
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Deshabilitar campos durante monitoreo
        if hasattr(self, 'ubicationInput'):
            self.ubicationInput.setEnabled(False)
        if hasattr(self, 'receiveInput'):
            self.receiveInput.setEnabled(False)
        
        # Simular actividad de monitoreo
        self.monitoring_timer = QTimer()
        self.monitoring_value = 0
        self.monitoring_timer.timeout.connect(self.update_monitoring_progress)
        self.monitoring_timer.start(100)
        
    def update_monitoring_progress(self):
        """Actualiza la barra de progreso de monitoreo"""
        self.monitoring_value = (self.monitoring_value + 1) % 100
        self.progress_bar.setValue(self.monitoring_value)
        
    def stop_monitoring_animation(self):
        """Detiene animación de monitoreo"""
        # Detener timer
        if hasattr(self, 'monitoring_timer'):
            self.monitoring_timer.stop()
            
        # Restaurar botón
        self.startMonitoring.setText("▶ Iniciar Monitoreo")
        self.startMonitoring.setStyleSheet(MonitoringWindowStyles.MONITORING_BUTTON)
        
        # Ocultar barra de progreso
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        
        # Rehabilitar campos
        if hasattr(self, 'ubicationInput'):
            self.ubicationInput.setEnabled(True)
        if hasattr(self, 'receiveInput'):
            self.receiveInput.setEnabled(True)
        
        # Revalidar formulario
        self.validate_form()

    def stopMonitoring(self):
        """Método original mejorado"""
        self.stop_monitoring_animation()
        self.is_monitoring = False
        logging.info("Monitoreo detenido")

    def logout(self):
        """Método original con confirmación mejorada"""
        if self.is_monitoring:
            reply = QMessageBox.question(self, 'Confirmar Logout', 
                                       'El monitoreo está activo. ¿Está seguro de que desea cerrar sesión?',
                                       QMessageBox.Yes | QMessageBox.No, 
                                       QMessageBox.No)
            if reply == QMessageBox.No:
                return
                
        logging.info("Usuario cerrando sesión")
        self.is_monitoring = False
        if hasattr(self, 'monitoring_timer'):
            self.monitoring_timer.stop()
        self.logoutSignal.emit()

    def showErrorMessage(self, title, message):
        """Método de mostrar errores con mejoras visuales y responsive"""            
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
        min_width = 400
        max_width = 600
        
        calculated_width = max(min_width, min(max_width, max_line_length * char_width + 100))
        calculated_height = max(180, num_lines * line_height + 120)
        
        error_box.setText(title)
        error_box.setInformativeText(message)
        
        # Aplicar estilo usando el método del archivo de estilos
        style = MonitoringWindowStyles.get_message_box_style(calculated_width, calculated_height, max_width)
        error_box.setStyleSheet(style)
        
        error_box.exec_()
        logging.warning(f"Error mostrado al usuario: {title} - {message}")

    def closeEvent(self, event):
        """Evento de cierre mejorado"""
        if self.is_monitoring:
            reply = QMessageBox.question(self, 'Confirmar Cierre', 
                                       'El monitoreo está activo. ¿Está seguro de que desea cerrar la ventana?',
                                       QMessageBox.Yes | QMessageBox.No, 
                                       QMessageBox.No)
            if reply == QMessageBox.No:
                event.ignore()
                return
                
        if hasattr(self, 'monitoring_timer'):
            self.monitoring_timer.stop()
            
        logging.info("Ventana de monitoreo cerrada")
        super().closeEvent(event)