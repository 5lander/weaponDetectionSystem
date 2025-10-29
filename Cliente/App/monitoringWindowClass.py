# -*- coding: utf-8 -*-
"""
monitoringWindowClass.py - VERSIÓN COMPLETAMENTE ESCALABLE
Soporta cualquier número de cámaras dinámicamente
"""

import sys
import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QLabel, QLineEdit, 
                             QPushButton, QComboBox, QCheckBox, QGroupBox,
                             QVBoxLayout, QHBoxLayout, QFormLayout, QMessageBox,
                             QTabWidget, QFrame, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
import logging
import cv2

# Importar configuración de cámaras
from .cameras_config import (CAMERAS_CONFIG, GLOBAL_CONFIG, get_enabled_cameras,
                             get_total_cameras, get_camera_number)


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
        
        self.setupUI()
        self.load_camera_configs()
        
        total_cams = get_total_cameras()
        logging.info(f"MonitoringWindow inicializada - {total_cams} cámara(s) detectada(s)")
    
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
        total_cameras = get_total_cameras()
        
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
        
        # Crear tabs dinámicamente según CAMERAS_CONFIG
        for camera_key in sorted(CAMERAS_CONFIG.keys(), 
                                key=lambda x: get_camera_number(x)):
            camera_num = get_camera_number(camera_key)
            camera_name = CAMERAS_CONFIG[camera_key].get('name', f'Cámara {camera_num}')
            
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
        
        # Contacto para notificaciones
        self.receiveInput = QLineEdit()
        self.receiveInput.setPlaceholderText("correo@ejemplo.com o +593987654321")
        self.receiveInput.setFont(QFont("Segoe UI", 10))
        self.receiveInput.setMinimumHeight(40)
        
        global_layout.addRow("📧 Receptor de Alertas:", self.receiveInput)
        global_group.setLayout(global_layout)
        main_layout.addWidget(global_group)
        
        # ==========================================
        # ESTADÍSTICAS
        # ==========================================
        stats_layout = QHBoxLayout()
        
        enabled_count = len([c for c in CAMERAS_CONFIG.values() if c.get('enabled', True)])
        
        stats_label = QLabel(
            f"📊 Total: {total_cameras} | "
            f"✅ Habilitadas: {enabled_count} | "
            f"⚪ Deshabilitadas: {total_cameras - enabled_count}"
        )
        stats_label.setFont(QFont("Segoe UI", 9))
        stats_label.setStyleSheet("color: #34495e; padding: 5px;")
        
        stats_layout.addWidget(stats_label)
        main_layout.addLayout(stats_layout)
        
        # ==========================================
        # BOTONES DE ACCIÓN
        # ==========================================
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
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
        widgets['enabled'] = enable_checkbox
        
        status_layout.addWidget(enable_checkbox)
        status_layout.addStretch()
        status_group.setLayout(status_layout)
        tab_layout.addWidget(status_group)
        
        # ==========================================
        # CONFIGURACIÓN RTSP
        # ==========================================
        rtsp_group = QGroupBox("🌐 Configuración de Red")
        rtsp_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        rtsp_group.setMinimumHeight(380)
        rtsp_layout = QFormLayout()
        rtsp_layout.setSpacing(15)
        rtsp_layout.setContentsMargins(20, 20, 20, 20)
        
        # IP
        ip_input = QLineEdit()
        ip_input.setPlaceholderText("192.168.1.10")
        ip_input.setFont(QFont("Segoe UI", 10))
        ip_input.setMinimumHeight(45)
        widgets['ip'] = ip_input
        
        # Usuario
        user_input = QLineEdit()
        user_input.setPlaceholderText("Usuario de Camera Account")
        user_input.setFont(QFont("Segoe UI", 10))
        user_input.setMinimumHeight(45)
        widgets['username'] = user_input
        
        # Contraseña
        pass_input = QLineEdit()
        pass_input.setPlaceholderText("Contraseña")
        pass_input.setFont(QFont("Segoe UI", 10))
        pass_input.setMinimumHeight(45)
        pass_input.setEchoMode(QLineEdit.Password)
        widgets['password'] = pass_input
        
        # Checkbox mostrar contraseña
        show_pass = QCheckBox("Mostrar contraseña")
        show_pass.setFont(QFont("Segoe UI", 9))
        show_pass.stateChanged.connect(
            lambda state: pass_input.setEchoMode(
                QLineEdit.Normal if state == Qt.Checked else QLineEdit.Password
            )
        )
        
        # Calidad de stream
        stream_combo = QComboBox()
        stream_combo.addItems([
            "Alta Calidad (stream1) - 2304x1296",
            "Baja Calidad (stream2) - 640x360"
        ])
        stream_combo.setFont(QFont("Segoe UI", 10))
        stream_combo.setMinimumHeight(45)
        widgets['stream'] = stream_combo
        
        rtsp_layout.addRow("🌐 IP:", ip_input)
        rtsp_layout.addRow("👤 Usuario:", user_input)
        rtsp_layout.addRow("🔒 Contraseña:", pass_input)
        rtsp_layout.addRow("", show_pass)
        rtsp_layout.addRow("📺 Calidad:", stream_combo)
        
        rtsp_group.setLayout(rtsp_layout)
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
        """Cargar configuraciones de cámaras desde archivo"""
        try:
            for camera_key, config in CAMERAS_CONFIG.items():
                if camera_key in self.camera_widgets:
                    widgets = self.camera_widgets[camera_key]
                    
                    widgets['ip'].setText(config.get('ip', ''))
                    widgets['username'].setText(config.get('username', ''))
                    widgets['password'].setText(config.get('password', ''))
                    widgets['location'].setText(config.get('location', ''))
                    widgets['enabled'].setChecked(config.get('enabled', True))
                    
                    if config.get('stream') == 'stream2':
                        widgets['stream'].setCurrentIndex(1)
            
            logging.info(f"Configuraciones cargadas para {len(self.camera_widgets)} cámara(s)")
            
        except Exception as e:
            logging.error(f"Error al cargar configuraciones: {e}")
    
    def get_camera_config(self, camera_key):
        """Obtener configuración de una cámara"""
        if camera_key not in self.camera_widgets:
            return None
        
        widgets = self.camera_widgets[camera_key]
        camera_num = get_camera_number(camera_key)
        stream_idx = widgets['stream'].currentIndex()
        
        return {
            'name': CAMERAS_CONFIG[camera_key].get('name', f'Cámara {camera_num}'),
            'ip': widgets['ip'].text(),
            'username': widgets['username'].text(),
            'password': widgets['password'].text(),
            'stream': 'stream1' if stream_idx == 0 else 'stream2',
            'port': 554,
            'location': widgets['location'].text(),
            'enabled': widgets['enabled'].isChecked()
        }
    
    def test_camera(self, camera_key):
        """Probar conexión de una cámara individual"""
        config = self.get_camera_config(camera_key)
        camera_num = get_camera_number(camera_key)
        
        if not config['enabled']:
            QMessageBox.information(
                self, "Cámara Deshabilitada",
                f"La cámara {camera_num} está deshabilitada."
            )
            return
        
        # Validar campos
        if not config['ip'] or not config['username'] or not config['password']:
            QMessageBox.warning(
                self, "Campos Incompletos",
                f"Complete todos los campos de la cámara {camera_num}."
            )
            return
        
        # Construir URL RTSP
        rtsp_url = f"rtsp://{config['username']}:{config['password']}@{config['ip']}:554/{config['stream']}"
        
        QMessageBox.information(
            self, "Probando Conexión",
            f"Conectando a cámara {camera_num}...\nEsto puede tardar unos segundos."
        )
        
        try:
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
                "rtsp_transport;udp|fflags;nobuffer|flags;low_delay"
            )
            
            cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
            
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    
                    QMessageBox.information(
                        self, f"✅ Cámara {camera_num} Conectada",
                        f"¡Conexión exitosa!\n\n"
                        f"Resolución: {width}x{height}\n"
                        f"IP: {config['ip']}\n"
                        f"Stream: {config['stream']}"
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
                                key=lambda x: get_camera_number(x)):
            config = self.get_camera_config(camera_key)
            camera_num = get_camera_number(camera_key)
            
            if not config['enabled']:
                results.append(f"Cámara {camera_num}: ⚪ Deshabilitada")
                continue
            
            if not config['ip'] or not config['username'] or not config['password']:
                results.append(f"Cámara {camera_num}: ⚠️ Campos incompletos")
                continue
            
            # Probar conexión
            rtsp_url = f"rtsp://{config['username']}:{config['password']}@{config['ip']}:554/{config['stream']}"
            
            try:
                os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
                    "rtsp_transport;udp|fflags;nobuffer|flags;low_delay"
                )
                
                cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
                
                if cap.isOpened():
                    ret, _ = cap.read()
                    if ret:
                        results.append(f"Cámara {camera_num}: ✅ OK ({config['ip']})")
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
    
    def start_monitoring_system(self):
        """Iniciar sistema de monitoreo multi-cámara"""
        # Validar receptor
        if not self.receiveInput.text():
            QMessageBox.warning(
                self, "Campo Requerido",
                "Ingrese un receptor para las alertas."
            )
            return
        
        # Recopilar cámaras habilitadas y configuradas
        enabled_cameras = []
        
        for camera_key in sorted(self.camera_widgets.keys(), 
                                key=lambda x: get_camera_number(x)):
            config = self.get_camera_config(camera_key)
            camera_num = get_camera_number(camera_key)
            
            if config['enabled']:
                if not config['ip'] or not config['username'] or not config['password'] or not config['location']:
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
            'receiver': self.receiveInput.text(),
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