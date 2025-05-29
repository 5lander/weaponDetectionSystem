# detectionWindow.py - VERSIÓN CORREGIDA SIN SEGMENTATION FAULT

from PyQt5.QtWidgets import (QMainWindow, QLabel, QFrame, QWidget, 
                            QProgressBar, QMessageBox, QVBoxLayout, QHBoxLayout, QPushButton)
from PyQt5.QtCore import (pyqtSignal, pyqtSlot, Qt, QTimer, QMutex, QMutexLocker,
                         QPropertyAnimation, QEasingCurve, QRect)
from PyQt5.QtGui import QImage, QPixmap, QFont, QIcon
from PyQt5.uic import loadUi
from App.detection import Detection
import os
import sys
import logging
import gc

# Importar los estilos desde la carpeta Styles
from Styles.detectionWindowStyle import (DetectionWindowStyles, 
                                       DetectionStatusStyles, 
                                       ResourceIndicatorStyles)

class StatusIndicator(QLabel):
    """Indicador de estado de detección moderno"""
    def __init__(self, initial_status="stopped", parent=None):
        super().__init__(parent)
        self.setFixedSize(15, 15)
        self.status = initial_status
        self.set_status(initial_status)
        
    def set_status(self, status):
        """Establece el estado y aplica el estilo correspondiente"""
        self.status = status
        style = DetectionStatusStyles.get_status_style(status)
        self.setStyleSheet(style)

class DetectionWindow(QMainWindow):
    closed = pyqtSignal()
    goBack = pyqtSignal()

    def __init__(self, token, location, receiver):
        super(DetectionWindow, self).__init__()
        
        # Variables de control para evitar segmentation fault
        self._is_closing = False
        self._detection_mutex = QMutex()
        self._cleanup_timer = QTimer()
        self._cleanup_timer.setSingleShot(True)
        self._cleanup_timer.timeout.connect(self._safe_cleanup)
        
        # Configurar resource_path
        self.setup_resource_path()
        
        # Cargar UI original
        ui_file = self.resource_path('UI/monitoringCameraWindow.ui')
        
        # Verificar si el archivo UI existe
        if not os.path.exists(ui_file):
            logging.error(f"Archivo UI no encontrado: {ui_file}")
            self.create_ui_programmatically()
        else:
            try:
                loadUi(ui_file, self)
            except Exception as e:
                logging.error(f"Error cargando UI: {e}")
                self.create_ui_programmatically()
        
        # Configurar parámetros
        self.token = token
        self.location = location
        self.receiver = receiver
        self.model_path = self.resource_path("model/predict.pt")
        self.detection = None
        
        # Configurar ventana como redimensionable
        self.setup_resizable_window()
        
        # Configurar título personalizado
        self.customize_title_bar()
        
        # Crear todos los componentes primero
        self.create_all_components()
        
        # Luego aplicar estilos y posicionamiento
        self.apply_modern_styling()
        self.setup_animations()
        
        # Conectar eventos
        self.setup_button_connections()
        
        # Timer para retrasar la creación de la instancia de detección
        self._init_timer = QTimer()
        self._init_timer.setSingleShot(True)
        self._init_timer.timeout.connect(self.createDetectionInstance)
        self._init_timer.start(500)  # Esperar 500ms antes de iniciar detección
        
        logging.info("DetectionWindow inicializada con protección contra segmentation fault")

    def setup_resource_path(self):
        """Configura el método resource_path"""
        if hasattr(sys, '_MEIPASS'):
            self.base_path = sys._MEIPASS
        else:
            self.base_path = os.path.abspath(".")
    
    def resource_path(self, relative_path):
        """Obtiene la ruta completa del recurso"""
        return os.path.join(self.base_path, relative_path)

    def setup_resizable_window(self):
        """Configura la ventana como redimensionable"""
        self.setMinimumSize(1000, 600)
        self.resize(1000, 600)
        self.setMaximumSize(16777215, 16777215)

    def create_ui_programmatically(self):
        """Crea la UI programáticamente si no existe el archivo .ui"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        self.CameraLabel = QLabel(central_widget)
        self.CameraLabel.setAlignment(Qt.AlignCenter)
        
        self.stopButton = QPushButton("🛑 Stop Monitoring", central_widget)
        self.backButton = QPushButton("← Back", central_widget)
        
        font = QFont("Segoe UI")
        self.setFont(font)

    def customize_title_bar(self):
        """Personaliza la barra de título de la ventana"""
        self.setWindowTitle("Weapon Detection System - Monitoring")
        try:
            icon_path = self.resource_path('UI/icon.ico')
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            logging.warning(f"No se pudo cargar el icono: {e}")

    def create_all_components(self):
        """Crea todos los componentes de la interfaz en el orden correcto"""
        try:
            self.add_title_bar()
            self.add_detection_status_indicator() 
            self.add_system_info_panel()
            self.setup_resource_labels()
            self.add_back_button()
            self.position_components()
        except Exception as e:
            logging.error(f"Error creando componentes: {e}")

    def apply_modern_styling(self):
        """Aplica estilos modernos usando los estilos separados"""
        try:
            self.setStyleSheet(DetectionWindowStyles.MAIN_WINDOW)
            if hasattr(self, 'CameraLabel'):
                self.CameraLabel.setStyleSheet(DetectionWindowStyles.CAMERA_LABEL)
            if hasattr(self, 'stopButton'):
                self.stopButton.setStyleSheet(DetectionWindowStyles.STOP_BUTTON)
        except Exception as e:
            logging.error(f"Error aplicando estilos: {e}")

    def add_title_bar(self):
        """Añade una barra de título moderna bien posicionada"""
        self.title_label = QLabel("🔍 Weapon Detection System", self)
        self.title_label.setStyleSheet(DetectionWindowStyles.TITLE_LABEL)
        
    def add_detection_status_indicator(self):
        """Añade indicador de estado de detección centrado"""
        self.status_frame = QFrame(self)
        self.status_frame.setStyleSheet(DetectionWindowStyles.DETECTION_INFO_FRAME)
        
        self.status_indicator = StatusIndicator("stopped", self.status_frame)
        
        self.status_text = QLabel("Stopped", self.status_frame)
        self.status_text.setStyleSheet(DetectionWindowStyles.DETECTION_INFO_LABEL)

    def add_system_info_panel(self):
        """Añade panel de información del sistema en la esquina superior derecha"""
        self.resources_frame = QFrame(self)
        self.resources_frame.setStyleSheet(DetectionWindowStyles.SYSTEM_RESOURCES_FRAME)
        
        self.resources_title = QLabel("📊 System Resources", self.resources_frame)
        self.resources_title.setStyleSheet(DetectionWindowStyles.DETECTION_INFO_LABEL)
        self.resources_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        
    def setup_resource_labels(self):
        """Configura las etiquetas de recursos del sistema"""
        if not hasattr(self, 'resources_frame'):
            logging.error("resources_frame no existe al crear resource labels")
            return
            
        self.cpuLabel = QLabel("CPU: 0%", self.resources_frame)
        self.memoryLabel = QLabel("Memory: 0%", self.resources_frame)
        self.gpuLabel = QLabel("GPU: 0%", self.resources_frame)
        
        self.cpuLabel.setStyleSheet(DetectionWindowStyles.CPU_LABEL)
        self.memoryLabel.setStyleSheet(DetectionWindowStyles.MEMORY_LABEL)
        self.gpuLabel.setStyleSheet(DetectionWindowStyles.GPU_LABEL)

    def add_back_button(self):
        """Añade botón de volver"""
        self.backButton = QPushButton("← Back", self)
        self.backButton.setStyleSheet(DetectionWindowStyles.BACK_BUTTON)
        self.backButton.setVisible(False)

    def setup_button_connections(self):
        """Configura las conexiones de los botones"""
        if hasattr(self, 'stopButton'):
            self.stopButton.clicked.connect(self.stop_detection_and_show_back)
        if hasattr(self, 'backButton'):
            self.backButton.clicked.connect(self.go_back_to_previous)

    def position_components(self):
        """Posiciona todos los componentes de manera responsive"""
        self.update_component_positions()

    def update_component_positions(self):
        """Actualiza las posiciones de los componentes según el tamaño de la ventana"""
        if self._is_closing:
            return
            
        try:
            window_width = self.width()
            window_height = self.height()
            
            if not hasattr(self, 'title_label'):
                return
                
            # Título en esquina superior izquierda
            if hasattr(self, 'title_label'):
                self.title_label.setGeometry(20, 15, 350, 40)
            
            # Estado de detección centrado en la parte superior
            if hasattr(self, 'status_frame'):
                status_width = 180
                status_x = (window_width - status_width) // 2
                self.status_frame.setGeometry(status_x, 15, status_width, 35)
                
                if hasattr(self, 'status_indicator'):
                    self.status_indicator.move(12, 10)
                if hasattr(self, 'status_text'):
                    self.status_text.setGeometry(35, 7, 135, 21)
            
            # Panel de recursos en esquina superior derecha
            if hasattr(self, 'resources_frame'):
                resources_width = 250
                resources_x = window_width - resources_width - 20
                self.resources_frame.setGeometry(resources_x, 15, resources_width, 130)
                
                if hasattr(self, 'resources_title'):
                    self.resources_title.setGeometry(10, 8, 230, 30)
                
                if hasattr(self, 'cpuLabel'):
                    self.cpuLabel.setGeometry(15, 40, 220, 28)
                if hasattr(self, 'memoryLabel'):
                    self.memoryLabel.setGeometry(15, 68, 220, 28)
                if hasattr(self, 'gpuLabel'):
                    self.gpuLabel.setGeometry(15, 96, 220, 28)
            
            # Cámara centrada
            if hasattr(self, 'CameraLabel'):
                camera_size = min(640, window_width - 100, window_height - 200)
                camera_x = (window_width - camera_size) // 2
                camera_y = 70
                self.CameraLabel.setGeometry(camera_x, camera_y, camera_size, camera_size)
            
            # Botones centrados en la parte inferior
            button_y = window_height - 70
            
            if hasattr(self, 'stopButton') and hasattr(self, 'backButton'):
                if self.backButton.isVisible():
                    button_width = 150
                    total_width = button_width * 2 + 20
                    start_x = (window_width - total_width) // 2
                    
                    self.backButton.setGeometry(start_x, button_y, button_width, 45)
                    self.stopButton.setGeometry(start_x + button_width + 20, button_y, button_width, 45)
                else:
                    button_width = 200
                    button_x = (window_width - button_width) // 2
                    self.stopButton.setGeometry(button_x, button_y, button_width, 45)
                    
        except Exception as e:
            logging.error(f"Error actualizando posiciones: {e}")

    def setup_animations(self):
        """Configura animaciones suaves"""
        try:
            self.setWindowOpacity(0)
            self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
            self.fade_animation.setDuration(700)
            self.fade_animation.setStartValue(0)
            self.fade_animation.setEndValue(1)
            self.fade_animation.setEasingCurve(QEasingCurve.OutQuart)
            self.fade_animation.start()
        except Exception as e:
            logging.error(f"Error configurando animaciones: {e}")
            self.setWindowOpacity(1)

    def resizeEvent(self, event):
        """Maneja el redimensionamiento de la ventana"""
        if not self._is_closing:
            super().resizeEvent(event)
            self.update_component_positions()

    def createDetectionInstance(self):
        """Crea la instancia de detección con protección contra segmentation fault"""
        if self._is_closing or self.detection is not None:
            return
            
        with QMutexLocker(self._detection_mutex):
            try:
                # Actualizar estado visual
                if hasattr(self, 'status_indicator'):
                    self.status_indicator.set_status("monitoring")
                if hasattr(self, 'status_text'):
                    self.status_text.setText("Starting...")
                
                # Crear instancia con verificación de path
                if not os.path.exists(self.model_path):
                    logging.error(f"Modelo no encontrado: {self.model_path}")
                    self.handleDetectionError(f"Model file not found: {self.model_path}")
                    return
                
                self.detection = Detection(self.model_path, self.token, self.location, self.receiver)
                
                # Conectar señales de forma segura
                self.detection.changePixmap.connect(self.setImage, Qt.QueuedConnection)
                self.detection.resourceUpdate.connect(self.updateResourceInfo, Qt.QueuedConnection)
                self.detection.error.connect(self.handleDetectionError, Qt.QueuedConnection)
                
                # Iniciar detección
                self.detection.start()
                
                # Actualizar estado después de iniciar con timer
                QTimer.singleShot(2000, self._update_detection_status)
                
                logging.info("Instancia de Detection creada y iniciada de forma segura")
                
            except Exception as e:
                logging.error(f"Error creando instancia de detección: {e}")
                self.handleDetectionError(f"Failed to create detection instance: {str(e)}")

    def _update_detection_status(self):
        """Actualiza el estado de detección de forma segura"""
        if not self._is_closing and hasattr(self, 'status_indicator'):
            try:
                self.status_indicator.set_status("detecting")
                if hasattr(self, 'status_text'):
                    self.status_text.setText("Active")
            except Exception as e:
                logging.error(f"Error actualizando estado: {e}")

    @pyqtSlot(QImage)
    def setImage(self, image):
        """Establece la imagen en el label de la cámara manteniendo proporción"""
        if self._is_closing or not hasattr(self, 'CameraLabel'):
            return
            
        try:
            pixmap = QPixmap.fromImage(image)
            scaled_pixmap = pixmap.scaled(
                self.CameraLabel.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.CameraLabel.setPixmap(scaled_pixmap)
        except Exception as e:
            logging.error(f"Error estableciendo imagen: {e}")

    @pyqtSlot(dict)
    def updateResourceInfo(self, resources):
        """Actualiza la información de recursos con protección contra errores"""
        if self._is_closing or not all(hasattr(self, attr) for attr in ['cpuLabel', 'memoryLabel', 'gpuLabel']):
            return
            
        try:
            cpu_usage = resources.get('cpu', 0)
            memory_usage = resources.get('memory', 0)
            gpu_usage = resources.get('gpu_load', 0)
            
            self.cpuLabel.setText(f"CPU: {cpu_usage:.1f}%")
            self.memoryLabel.setText(f"Memory: {memory_usage:.1f}%")
            self.gpuLabel.setText(f"GPU: {gpu_usage:.1f}%")
            
            self.cpuLabel.setStyleSheet(
                ResourceIndicatorStyles.get_resource_style_by_level("cpu", cpu_usage)
            )
            self.memoryLabel.setStyleSheet(
                ResourceIndicatorStyles.get_resource_style_by_level("memory", memory_usage)
            )
            self.gpuLabel.setStyleSheet(
                ResourceIndicatorStyles.get_resource_style_by_level("gpu", gpu_usage)
            )
        except Exception as e:
            logging.error(f"Error actualizando recursos: {e}")

    @pyqtSlot(str)
    def handleDetectionError(self, error_message):
        """Maneja errores de detección con alertas visuales mejoradas"""
        if self._is_closing:
            return
            
        logging.error(f"Error en la detección: {error_message}")
        
        try:
            if hasattr(self, 'status_indicator'):
                self.status_indicator.set_status("error")
            if hasattr(self, 'status_text'):
                self.status_text.setText("Error")
            
            self.showErrorMessage("Detection Error", error_message)
        except Exception as e:
            logging.error(f"Error manejando error de detección: {e}")

    def showErrorMessage(self, title, message):
        """Muestra mensajes de error con estilo mejorado"""
        if self._is_closing:
            return
            
        try:
            error_box = QMessageBox(self)
            error_box.setIcon(QMessageBox.Critical)
            error_box.setWindowTitle(title)
            error_box.setText(title)
            error_box.setInformativeText(message)
            
            style = DetectionWindowStyles.get_alert_message_style("danger")
            error_box.setStyleSheet(style)
            
            error_box.exec_()
        except Exception as e:
            logging.error(f"Error mostrando mensaje de error: {e}")

    def stop_detection_and_show_back(self):
        """Detiene la detección y muestra el botón de volver"""
        if self._is_closing:
            return
            
        self.close_detection()
        
        try:
            if hasattr(self, 'backButton') and hasattr(self, 'stopButton'):
                self.backButton.setVisible(True)
                self.stopButton.setText("🔄 Restart Monitoring")
                
                # Desconectar señal anterior de forma segura
                try:
                    self.stopButton.clicked.disconnect()
                except:
                    pass
                    
                self.stopButton.clicked.connect(self.restart_detection)
                self.update_component_positions()
        except Exception as e:
            logging.error(f"Error en stop_detection_and_show_back: {e}")

    def restart_detection(self):
        """Reinicia la detección"""
        if self._is_closing:
            return
            
        try:
            if hasattr(self, 'backButton') and hasattr(self, 'stopButton'):
                self.backButton.setVisible(False)
                self.stopButton.setText("🛑 Stop Monitoring")
                
                # Desconectar señal anterior de forma segura
                try:
                    self.stopButton.clicked.disconnect()
                except:
                    pass
                    
                self.stopButton.clicked.connect(self.stop_detection_and_show_back)
            
            # Esperar un momento antes de reiniciar
            QTimer.singleShot(1000, self.createDetectionInstance)
            self.update_component_positions()
            
        except Exception as e:
            logging.error(f"Error reiniciando detección: {e}")

    def go_back_to_previous(self):
        """Vuelve a la ventana anterior"""
        if self._is_closing:
            return
            
        try:
            self.goBack.emit()
            self.close()
        except Exception as e:
            logging.error(f"Error volviendo a ventana anterior: {e}")

    def close_detection(self):
        """Detiene la detección con protección contra segmentation fault"""
        with QMutexLocker(self._detection_mutex):
            if self.detection is not None:
                try:
                    # Actualizar estado visual
                    if hasattr(self, 'status_indicator'):
                        self.status_indicator.set_status("stopped")
                    if hasattr(self, 'status_text'):
                        self.status_text.setText("Stopped")
                    
                    # Desconectar todas las señales de forma segura
                    try:
                        self.detection.changePixmap.disconnect()
                        self.detection.resourceUpdate.disconnect()
                        self.detection.error.disconnect()
                    except:
                        pass
                    
                    # Detener el hilo de detección de forma segura
                    self.detection.stop()
                    
                    # Esperar con timeout para evitar bloqueos
                    if not self.detection.wait(5000):  # 5 segundos timeout
                        logging.warning("Detection thread no terminó en tiempo esperado")
                        self.detection.terminate()
                        self.detection.wait(2000)  # Esperar 2 segundos más
                    
                    self.detection = None
                    logging.info("Detección detenida de forma segura")
                    
                    # Limpiar la imagen de la cámara
                    if hasattr(self, 'CameraLabel'):
                        self.CameraLabel.clear()
                        self.CameraLabel.setText("Detection Stopped\n\nClick 'Restart Monitoring' to continue")
                        self.CameraLabel.setStyleSheet(DetectionWindowStyles.CAMERA_LABEL + """
                            QLabel {
                                color: #94a3b8;
                                font-size: 16px;
                                font-weight: bold;
                            }
                        """)
                    
                    # Forzar recolección de basura
                    gc.collect()
                    
                except Exception as e:
                    logging.error(f"Error deteniendo detección: {e}")

    def _safe_cleanup(self):
        """Realiza limpieza segura de resources"""
        try:
            # Detener cualquier timer activo
            if hasattr(self, '_init_timer'):
                self._init_timer.stop()
            
            # Detener animaciones
            if hasattr(self, 'fade_animation'):
                self.fade_animation.stop()
            
            # Limpiar referencias
            self.detection = None
            
            # Forzar recolección de basura
            gc.collect()
            
            logging.info("Limpieza segura completada")
            
        except Exception as e:
            logging.error(f"Error en limpieza segura: {e}")

    def closeEvent(self, event):
        """Maneja el cierre de la ventana con protección contra segmentation fault"""
        if self._is_closing:
            event.accept()
            return
            
        self._is_closing = True
        logging.info("Iniciando cierre seguro de DetectionWindow")
        
        try:
            # Actualizar estado visual
            if hasattr(self, 'status_indicator'):
                self.status_indicator.set_status("stopped")
            if hasattr(self, 'status_text'):
                self.status_text.setText("Stopping...")
            
            # Detener detección de forma segura
            self.close_detection()
            
            # Iniciar timer de limpieza
            self._cleanup_timer.start(100)
            
            # Emitir señal de cierre
            self.closed.emit()
            
        except Exception as e:
            logging.error(f"Error en closeEvent: {e}")
        finally:
            # Aceptar el evento de cierre
            super().closeEvent(event)