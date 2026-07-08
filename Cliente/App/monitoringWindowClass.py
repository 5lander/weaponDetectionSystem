# -*- coding: utf-8 -*-
"""
monitoringWindowClass.py - VERSIÓN COMPLETAMENTE ESCALABLE
Soporta cualquier número de cámaras dinámicamente con gestor integrado
"""

import sys
import os
import json
from PyQt5.QtWidgets import (QMainWindow, QWidget, QLabel, QLineEdit, 
                             QPushButton, QComboBox, QCheckBox, QGroupBox,
                             QVBoxLayout, QHBoxLayout, QFormLayout, QMessageBox,
                             QTabWidget, QFrame, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
import logging
import cv2

from .rtsp_fields import RtspFieldsGroup
from . import rtsp_profiles as profiles

# Importar el gestor de cámaras
try:
    from .cameraManagerWindow import CameraManagerWindow
    CAMERA_MANAGER_AVAILABLE = True
except ImportError:
    CAMERA_MANAGER_AVAILABLE = False
    logging.warning("CameraManagerWindow no disponible - usando modo legacy")


class MonitoringWindow(QMainWindow):
    """
    Ventana de configuración ESCALABLE para sistema multi-cámara
    Detecta automáticamente el número de cámaras configuradas
    """
    startMonitoringSignal = pyqtSignal(dict)
    
    def __init__(self, token):
        super(MonitoringWindow, self).__init__()
        self.token = token
        self.detection_threads = {}
        
        # Diccionarios para almacenar widgets de cada cámara
        self.camera_widgets = {}
        
        # Cargar cámaras desde JSON
        self.cameras = self.load_cameras_from_json()
        
        self.setupUI()
        self.load_camera_configs()
        
        total_cams = len(self.cameras)
        logging.info(f"MonitoringWindow inicializada - {total_cams} cámara(s) detectada(s)")
    
    def load_cameras_from_json(self):
        """Cargar cámaras desde cameras.json"""
        config_file = 'cameras.json'
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    cameras = json.load(f)
                    logging.info(f"Cargadas {len(cameras)} cámaras desde cameras.json")
                    return cameras
            except Exception as e:
                logging.error(f"Error al cargar cameras.json: {e}")
                return self.get_default_cameras()
        
        # Si no existe, crear con configuración por defecto
        logging.info("cameras.json no encontrado, creando configuración por defecto")
        default_cameras = self.get_default_cameras()
        
        # Guardar default
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_cameras, f, indent=4, ensure_ascii=False)
            logging.info("Creado cameras.json con configuración por defecto")
        except Exception as e:
            logging.error(f"Error al crear cameras.json: {e}")
        
        return default_cameras
    
    def get_default_cameras(self):
        """Obtener configuración por defecto"""
        return {
            'camera_1': {
                'name': 'Cámara Principal',
                'ip': '192.168.1.10',
                'username': 'admin',
                'password': 'password',
                'stream': 'stream1',
                'port': 554,
                'location': 'Entrada Principal',
                'enabled': True
            }
        }
    
    def get_total_cameras(self):
        """Obtener número total de cámaras"""
        return len(self.cameras)
    
    def get_camera_number(self, camera_key):
        """Extraer número de cámara"""
        try:
            return int(camera_key.split('_')[1])
        except:
            return 0
    
    def setupUI(self):
        """Configurar interfaz de usuario DINÁMICA"""
        
        # Widget central con scroll
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # ==========================================
        # ENCABEZADO DINÁMICO
        # ==========================================
        total_cameras = self.get_total_cameras()
        
        header_layout = QVBoxLayout()
        
        title = QLabel(f"🎥 Sistema Multi-Cámara de Detección")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin: 10px;")
        
        subtitle = QLabel(f"Gestiona tus {total_cameras} cámara(s)")
        subtitle.setFont(QFont("Segoe UI", 10))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #7f8c8d; margin-bottom: 20px;")
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        main_layout.addLayout(header_layout)
        
        # Línea separadora
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #bdc3c7;")
        main_layout.addWidget(line)
        
        # ==========================================
        # TABS DINÁMICOS PARA CÁMARAS
        # ==========================================
        self.camera_tabs = QTabWidget()
        self.camera_tabs.setFont(QFont("Segoe UI", 10))
        
        # Crear tabs dinámicamente según cámaras en JSON
        for camera_key in sorted(self.cameras.keys(), 
                                key=lambda x: self.get_camera_number(x)):
            camera_num = self.get_camera_number(camera_key)
            camera_name = self.cameras[camera_key].get('name', f'Cámara {camera_num}')
            
            # Crear tab
            camera_widget = self.create_camera_tab(camera_key, camera_num)
            
            # Icono según el número
            icon = "📹" if camera_num <= 2 else "🎥"
            self.camera_tabs.addTab(camera_widget, f"{icon} {camera_name}")
            
            logging.info(f"Tab creado para {camera_key}: {camera_name}")
        
        main_layout.addWidget(self.camera_tabs)
        
        # ==========================================
        # CONFIGURACIÓN GLOBAL
        # ==========================================
        global_group = QGroupBox("⚙️ Configuración Global")
        global_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        global_layout = QFormLayout()
        
        # Contacto para notificaciones (solo correo electrónico)
        self.receiveInput = QLineEdit()
        self.receiveInput.setPlaceholderText("correo@ejemplo.com")
        self.receiveInput.setFont(QFont("Segoe UI", 10))
        self.receiveInput.setMinimumHeight(40)

        global_layout.addRow("📧 Correo para Alertas:", self.receiveInput)
        global_group.setLayout(global_layout)
        main_layout.addWidget(global_group)
        
        # ==========================================
        # ESTADÍSTICAS
        # ==========================================
        stats_layout = QHBoxLayout()
        
        enabled_count = len([c for c in self.cameras.values() if c.get('enabled', True)])
        
        # Se guarda como atributo para poder refrescarlo en tiempo real cuando
        # se marca/desmarca cualquier checkbox de habilitación.
        self.stats_label = QLabel(
            f"📊 Total: {total_cameras} | "
            f"✅ Habilitadas: {enabled_count} | "
            f"⚪ Deshabilitadas: {total_cameras - enabled_count}"
        )
        self.stats_label.setFont(QFont("Segoe UI", 9))
        self.stats_label.setStyleSheet("color: #34495e; padding: 5px;")

        stats_layout.addWidget(self.stats_label)
        main_layout.addLayout(stats_layout)
        
        # ==========================================
        # BOTONES DE ACCIÓN
        # ==========================================
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Botón Gestionar Cámaras (solo si está disponible)
        if CAMERA_MANAGER_AVAILABLE:
            self.manageCamerasButton = QPushButton("⚙️ Gestionar Cámaras")
            self.manageCamerasButton.setMinimumHeight(50)
            self.manageCamerasButton.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.manageCamerasButton.setStyleSheet("""
                QPushButton {
                    background-color: #9b59b6;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 10px;
                }
                QPushButton:hover {
                    background-color: #8e44ad;
                }
            """)
            self.manageCamerasButton.clicked.connect(self.open_camera_manager)
            button_layout.addWidget(self.manageCamerasButton)
        
        # Botón Probar Todas
        self.testAllButton = QPushButton("🔧 Probar Todas las Cámaras")
        self.testAllButton.setMinimumHeight(50)
        self.testAllButton.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.testAllButton.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.testAllButton.clicked.connect(self.test_all_cameras)
        
        # Botón Iniciar Sistema
        self.startButton = QPushButton(f"▶️ Iniciar Sistema ({enabled_count} cámaras)")
        self.startButton.setMinimumHeight(50)
        self.startButton.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.startButton.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        self.startButton.clicked.connect(self.start_monitoring_system)
        
        # Botón Cerrar Sesión
        self.logoutButton = QPushButton("🚪 Cerrar Sesión")
        self.logoutButton.setMinimumHeight(50)
        self.logoutButton.setFont(QFont("Segoe UI", 10))
        self.logoutButton.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.logoutButton.clicked.connect(self.logout)
        
        button_layout.addWidget(self.testAllButton)
        button_layout.addWidget(self.startButton)
        button_layout.addWidget(self.logoutButton)
        
        main_layout.addLayout(button_layout)
        
        # Configuración de ventana (tamaño adaptativo)
        window_height = min(900, 600 + (total_cameras * 50))
        self.setWindowTitle(f"Sistema Multi-Cámara ({total_cameras}) - Weapon Detection")
        self.setMinimumSize(900, window_height)
    
    def refresh_camera_stats(self):
        """Recalcular en tiempo real Total/Habilitadas/Deshabilitadas y el texto
        del botón "Iniciar Sistema", leyendo el estado actual de cada checkbox.

        Se invoca cada vez que se marca/desmarca un checkbox de habilitación y
        una vez al cargar la configuración inicial.
        """
        try:
            total = len(self.camera_widgets)
            enabled = sum(
                1 for w in self.camera_widgets.values()
                if w['enabled'].isChecked()
            )
            disabled = total - enabled

            if hasattr(self, 'stats_label'):
                self.stats_label.setText(
                    f"📊 Total: {total} | "
                    f"✅ Habilitadas: {enabled} | "
                    f"⚪ Deshabilitadas: {disabled}"
                )
            if hasattr(self, 'startButton'):
                self.startButton.setText(f"▶️ Iniciar Sistema ({enabled} cámaras)")
        except Exception as e:
            logging.exception(f"Error al refrescar estadísticas de cámaras: {e}")

    def create_camera_tab(self, camera_key, camera_num):
        """Crear tab de configuración para una cámara individual"""
        # Crear widget principal con scroll
        tab_widget = QWidget()
        tab_main_layout = QVBoxLayout(tab_widget)
        tab_main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        # Widget interno con contenido
        content_widget = QWidget()
        tab_layout = QVBoxLayout(content_widget)
        tab_layout.setSpacing(15)
        tab_layout.setContentsMargins(10, 10, 10, 10)
        
        # Diccionario para almacenar widgets de esta cámara
        widgets = {}
        
        # ==========================================
        # ESTADO DE CÁMARA
        # ==========================================
        status_group = QGroupBox(f"Estado de Cámara {camera_num}")
        status_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        status_layout = QHBoxLayout()
        
        # Checkbox habilitar
        enable_checkbox = QCheckBox(f"Habilitar Cámara {camera_num}")
        enable_checkbox.setChecked(True)
        enable_checkbox.setFont(QFont("Segoe UI", 10))
        # Recalcular contadores y texto del botón en tiempo real al alternar.
        enable_checkbox.stateChanged.connect(self.refresh_camera_stats)
        widgets['enabled'] = enable_checkbox
        
        status_layout.addWidget(enable_checkbox)
        status_layout.addStretch()
        status_group.setLayout(status_layout)
        tab_layout.addWidget(status_group)
        
        # ==========================================
        # CONFIGURACIÓN RTSP (marca, IP, puerto, usuario, contraseña, canal, calidad, ruta)
        # ==========================================
        rtsp_group = RtspFieldsGroup(title="🌐 Conexión de la cámara")
        widgets['fields'] = rtsp_group
        tab_layout.addWidget(rtsp_group)
        
        # ==========================================
        # UBICACIÓN
        # ==========================================
        location_group = QGroupBox("📍 Ubicación")
        location_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        location_layout = QFormLayout()
        location_layout.setSpacing(10)
        location_layout.setContentsMargins(20, 20, 20, 20)
        
        location_input = QLineEdit()
        location_input.setPlaceholderText(f"Ej: Zona {camera_num}")
        location_input.setFont(QFont("Segoe UI", 10))
        location_input.setMinimumHeight(45)
        widgets['location'] = location_input
        
        location_layout.addRow("Ubicación:", location_input)
        location_group.setLayout(location_layout)
        tab_layout.addWidget(location_group)
        
        # ==========================================
        # BOTÓN PROBAR INDIVIDUAL
        # ==========================================
        test_btn = QPushButton(f"🔧 Probar Cámara {camera_num}")
        test_btn.setMinimumHeight(50)
        test_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        test_btn.clicked.connect(lambda: self.test_camera(camera_key))
        tab_layout.addWidget(test_btn)
        
        tab_layout.addStretch()
        
        # Guardar widgets de esta cámara
        self.camera_widgets[camera_key] = widgets
        
        # Configurar scroll
        scroll.setWidget(content_widget)
        tab_main_layout.addWidget(scroll)
        
        return tab_widget
    
    def load_camera_configs(self):
        """Cargar configuraciones de cámaras desde JSON"""
        try:
            for camera_key, config in self.cameras.items():
                if camera_key in self.camera_widgets:
                    widgets = self.camera_widgets[camera_key]

                    widgets['fields'].set_config(config)
                    widgets['location'].setText(config.get('location', ''))
                    widgets['enabled'].setChecked(config.get('enabled', True))

            logging.info(f"Configuraciones cargadas para {len(self.camera_widgets)} cámara(s)")

            # Reflejar el estado real (enabled) recién cargado del JSON en el
            # resumen y en el texto del botón.
            self.refresh_camera_stats()

        except Exception as e:
            logging.error(f"Error al cargar configuraciones: {e}")
    
    def open_camera_manager(self):
        """Abrir ventana de gestión de cámaras"""
        if not CAMERA_MANAGER_AVAILABLE:
            QMessageBox.warning(
                self, "No Disponible",
                "El gestor de cámaras no está disponible.\n"
                "Edite manualmente el archivo cameras.json"
            )
            return
        
        try:
            manager = CameraManagerWindow(self)
            manager.camerasUpdated.connect(self.reload_cameras)
            manager.exec_()
        except Exception as e:
            logging.error(f"Error al abrir gestor de cámaras: {e}")
            QMessageBox.critical(
                self, "Error",
                f"Error al abrir gestor de cámaras:\n{str(e)}"
            )
    
    def reload_cameras(self):
        """Recargar cámaras después de cambios"""
        reply = QMessageBox.question(
            self, 'Recargar',
            'Las cámaras han sido actualizadas.\n'
            '¿Desea recargar la ventana para ver los cambios?\n\n'
            'Nota: Deberá volver a configurar el receptor de alertas.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            # Guardar receptor actual
            receiver = self.receiveInput.text()
            
            # Recargar
            self.cameras = self.load_cameras_from_json()
            self.camera_widgets.clear()
            
            # Recrear UI
            central = self.centralWidget()
            if central:
                central.deleteLater()
            
            self.setupUI()
            self.load_camera_configs()
            
            # Restaurar receptor
            self.receiveInput.setText(receiver)
            
            QMessageBox.information(
                self, "Recargado",
                "Ventana actualizada con las nuevas cámaras."
            )
    
    def get_camera_config(self, camera_key):
        """Obtener configuración de una cámara (identificación + conexión RTSP por marca)."""
        if camera_key not in self.camera_widgets:
            return None

        widgets = self.camera_widgets[camera_key]
        camera_num = self.get_camera_number(camera_key)

        config = {
            'name': self.cameras[camera_key].get('name', f'Cámara {camera_num}'),
            'location': widgets['location'].text(),
            'enabled': widgets['enabled'].isChecked(),
        }
        config.update(widgets['fields'].get_config())
        return config
    
    def test_camera(self, camera_key):
        """Probar conexión de una cámara individual"""
        config = self.get_camera_config(camera_key)
        camera_num = self.get_camera_number(camera_key)
        
        if not config['enabled']:
            QMessageBox.information(
                self, "Cámara Deshabilitada",
                f"La cámara {camera_num} está deshabilitada."
            )
            return
        
        # Validar campos (según la marca)
        brand = config.get('brand', 'tapo')
        if profiles.is_local_source(config):
            valid = True
        elif profiles.brand_uses_custom_path(brand):
            valid = bool((config.get('path') or '').strip())
        else:
            valid = bool(config['ip'] and config['username'] and config['password'])
        if not valid:
            QMessageBox.warning(
                self, "Campos Incompletos",
                f"Complete los datos de conexión de la cámara {camera_num}."
            )
            return

        # Construir URL RTSP según la marca
        rtsp_url = profiles.build_rtsp_url(config)

        QMessageBox.information(
            self, "Probando Conexión",
            f"Conectando a cámara {camera_num}...\nEsto puede tardar unos segundos."
        )

        try:
            if profiles.is_local_source(config):
                idx = profiles.local_device_index(config)
                if sys.platform.startswith('win'):
                    cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
                else:
                    cap = cv2.VideoCapture(idx)
            else:
                os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
                    "rtsp_transport;udp|fflags;nobuffer|flags;low_delay"
                )
                cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

                    fuente = (f"Webcam local (índice {profiles.local_device_index(config)})"
                              if profiles.is_local_source(config)
                              else f"IP: {config.get('ip', '')}")
                    QMessageBox.information(
                        self, f"✅ Cámara {camera_num} Conectada",
                        f"¡Conexión exitosa!\n\n"
                        f"Resolución: {width}x{height}\n"
                        f"{fuente}\n"
                        f"Marca: {profiles.brand_label(config.get('brand', 'tapo'))}"
                    )
                else:
                    QMessageBox.warning(
                        self, "Advertencia",
                        f"Se conectó pero no se pudieron leer frames.\n"
                        f"Verifique la cámara {camera_num}."
                    )
                cap.release()
            else:
                QMessageBox.critical(
                    self, f"❌ Error Cámara {camera_num}",
                    "No se pudo conectar.\n\nVerificar:\n"
                    "• IP correcta\n• Credenciales correctas\n"
                    "• Cámara encendida\n• Misma red WiFi"
                )
        
        except Exception as e:
            QMessageBox.critical(
                self, "Error",
                f"Error al probar cámara {camera_num}:\n{str(e)}"
            )
    
    def test_all_cameras(self):
        """Probar todas las cámaras configuradas"""
        results = []
        
        for camera_key in sorted(self.camera_widgets.keys(), 
                                key=lambda x: self.get_camera_number(x)):
            config = self.get_camera_config(camera_key)
            camera_num = self.get_camera_number(camera_key)
            
            if not config['enabled']:
                results.append(f"Cámara {camera_num}: ⚪ Deshabilitada")
                continue
            
            if not self._camera_config_is_complete(config):
                results.append(f"Cámara {camera_num}: ⚠️ Campos incompletos")
                continue

            # Probar conexión
            rtsp_url = profiles.build_rtsp_url(config)
            is_local = profiles.is_local_source(config)

            try:
                if is_local:
                    idx = profiles.local_device_index(config)
                    if sys.platform.startswith('win'):
                        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
                    else:
                        cap = cv2.VideoCapture(idx)
                else:
                    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
                        "rtsp_transport;udp|fflags;nobuffer|flags;low_delay"
                    )
                    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

                if cap.isOpened():
                    ret, _ = cap.read()
                    if ret:
                        fuente = (f"webcam {profiles.local_device_index(config)}"
                                  if is_local else config.get('ip', ''))
                        results.append(f"Cámara {camera_num}: ✅ OK ({fuente})")
                    else:
                        results.append(f"Cámara {camera_num}: ⚠️ Sin frames")
                    cap.release()
                else:
                    results.append(f"Cámara {camera_num}: ❌ No conecta")
            
            except Exception as e:
                results.append(f"Cámara {camera_num}: ❌ Error ({str(e)[:30]})")
        
        # Mostrar resultados
        msg = "RESULTADOS DE PRUEBA:\n\n" + "\n".join(results)
        QMessageBox.information(self, "Prueba de Cámaras", msg)
    
    def _is_valid_email(self, text):
        """Validación simple de correo electrónico"""
        text = text.strip()
        if '@' not in text:
            return False
        local, _, domain = text.partition('@')
        return bool(local) and '.' in domain and not domain.startswith('.') and not domain.endswith('.')

    def _camera_config_is_complete(self, config):
        """Validar que una cámara tenga los datos necesarios según su marca."""
        if not config.get('location'):
            return False
        brand = config.get('brand', 'tapo')
        if profiles.is_local_source(config):
            # Webcam local: solo necesita ubicación (ya validada arriba).
            return True
        if profiles.brand_uses_custom_path(brand):
            path = (config.get('path') or '').strip()
            if not path:
                return False
            # Si pegó la URL rtsp:// completa, no exige IP/credenciales aparte.
            if path.lower().startswith('rtsp://'):
                return True
            return bool(config.get('ip'))
        return bool(config.get('ip') and config.get('username') and config.get('password'))

    def start_monitoring_system(self):
        """Iniciar sistema de monitoreo multi-cámara"""
        # Validar correo de alertas (solo correo electrónico)
        receiver = self.receiveInput.text().strip()
        if not receiver:
            QMessageBox.warning(
                self, "Campo Requerido",
                "Ingrese un correo electrónico para recibir las alertas."
            )
            return
        if not self._is_valid_email(receiver):
            QMessageBox.warning(
                self, "Correo Inválido",
                "Ingrese un correo electrónico válido.\n\nEjemplo: nombre@dominio.com"
            )
            return
        
        # Recopilar cámaras habilitadas y configuradas
        enabled_cameras = []
        
        for camera_key in sorted(self.camera_widgets.keys(), 
                                key=lambda x: self.get_camera_number(x)):
            config = self.get_camera_config(camera_key)
            camera_num = self.get_camera_number(camera_key)
            
            if config['enabled']:
                if not self._camera_config_is_complete(config):
                    QMessageBox.warning(
                        self, f"Cámara {camera_num} Incompleta",
                        f"Complete todos los campos de la cámara {camera_num}."
                    )
                    return
                enabled_cameras.append((camera_num, config))
        
        if not enabled_cameras:
            QMessageBox.warning(
                self, "Sin Cámaras",
                "Habilite al menos una cámara para continuar."
            )
            return
        
        # Preparar configuración para enviar a main.py
        cameras_config = {
            'receiver': receiver,
            'token': self.token,
            'cameras': {}
        }
        
        for cam_num, config in enabled_cameras:
            cameras_config['cameras'][cam_num] = config
        
        # Emitir señal
        logging.info(f"Emitiendo señal de inicio con {len(enabled_cameras)} cámara(s)")
        self.startMonitoringSignal.emit(cameras_config)
    
    def logout(self):
        """Cerrar sesión"""
        reply = QMessageBox.question(
            self, 'Confirmar',
            '¿Desea cerrar sesión?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            logging.info("Usuario cerró sesión")
            self.close()