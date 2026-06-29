# -*- coding: utf-8 -*-
"""
detectionWindowDual.py - VISTA ESCALABLE CON GRID DINÁMICO
Soporta 1 a N cámaras con distribución inteligente
"""

import sys
import math
from PyQt5.QtWidgets import (QMainWindow, QWidget, QLabel, QPushButton,
                             QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
                             QMessageBox, QFrame, QScrollArea)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap
import logging


class DetectionWindowDual(QMainWindow):
    """
    Ventana optimizada para mostrar N cámaras en grid dinámico
    - 1 cámara: Pantalla completa
    - 2 cámaras: 1x2 (lado a lado)
    - 3-4 cámaras: Grid 2x2
    - 5-6 cámaras: Grid 2x3
    - 7-9 cámaras: Grid 3x3
    - 10+ cámaras: Scroll vertical
    """
    
    closed = pyqtSignal()
    
    def __init__(self, detection_threads):
        """
        Args:
            detection_threads: Dict {camera_id: DetectionTapo_instance}
        """
        super(DetectionWindowDual, self).__init__()
        
        self.detection_threads = detection_threads
        self.num_cameras = len(detection_threads)

        # Evita preguntar dos veces al cerrar (botón -> close() -> closeEvent)
        self._is_closing = False
        
        # Widgets para cada cámara
        self.camera_labels = {}
        self.status_labels = {}
        self.fps_labels = {}
        self.detection_labels = {}
        
        # Calcular dimensiones de grid
        self.grid_rows, self.grid_cols = self.calculate_grid_dimensions()
        
        self.setupUI()
        self.start_detections()
        
        # Timer para actualizar métricas
        self.metrics_timer = QTimer()
        self.metrics_timer.timeout.connect(self.update_metrics)
        self.metrics_timer.start(1000)
        
        logging.info(f"DetectionWindow con {self.num_cameras} cámara(s) - Grid {self.grid_rows}x{self.grid_cols}")
    
    def calculate_grid_dimensions(self):
        """Calcular dimensiones óptimas del grid según número de cámaras"""
        n = self.num_cameras
        
        if n == 1:
            return 1, 1
        elif n == 2:
            return 1, 2
        elif n <= 4:
            return 2, 2
        elif n <= 6:
            return 2, 3
        elif n <= 9:
            return 3, 3
        elif n <= 12:
            return 3, 4
        elif n <= 16:
            return 4, 4
        else:
            # Para más de 16, usar grid de 4 columnas con scroll
            cols = 4
            rows = math.ceil(n / cols)
            return rows, cols
    
    def calculate_camera_size(self):
        """Calcular tamaño de cada cámara según el grid.

        Tamaños ajustados para que todas las cámaras quepan en pantalla
        (la ventana se abre maximizada y el grid tiene scroll para el resto).
        """
        if self.num_cameras == 1:
            return 900, 640
        elif self.num_cameras == 2:
            return 620, 460
        elif self.num_cameras <= 4:
            return 460, 345
        elif self.num_cameras <= 6:
            return 400, 300
        elif self.num_cameras <= 9:
            return 320, 240
        else:
            return 280, 210
    
    def setupUI(self):
        """Configurar interfaz de usuario DINÁMICA"""
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # ==========================================
        # ENCABEZADO
        # ==========================================
        header_layout = QHBoxLayout()
        
        title = QLabel(f"🎥 Monitoreo de {self.num_cameras} Cámara(s)")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color: #2c3e50;")
        
        # Indicador de sistema activo
        self.system_status = QLabel("● SISTEMA ACTIVO")
        self.system_status.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.system_status.setStyleSheet("color: #27ae60;")
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.system_status)
        
        main_layout.addLayout(header_layout)
        
        # Línea separadora
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #bdc3c7;")
        main_layout.addWidget(line)
        
        # ==========================================
        # SCROLL AREA PARA GRID DE CÁMARAS
        # ==========================================
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        # Widget del grid
        grid_widget = QWidget()
        cameras_layout = QGridLayout(grid_widget)
        cameras_layout.setSpacing(10)
        
        # Calcular tamaño de cámaras
        cam_width, cam_height = self.calculate_camera_size()
        
        # Crear widgets de cámaras en grid
        sorted_cameras = sorted(self.detection_threads.keys())
        
        for idx, cam_id in enumerate(sorted_cameras):
            row = idx // self.grid_cols
            col = idx % self.grid_cols
            
            cam_widget = self.create_camera_widget(cam_id, cam_width, cam_height)
            cameras_layout.addWidget(cam_widget, row, col)
        
        scroll.setWidget(grid_widget)
        main_layout.addWidget(scroll)
        
        # ==========================================
        # PANEL DE INFORMACIÓN GLOBAL
        # ==========================================
        info_group = QGroupBox("📊 Información del Sistema")
        info_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        info_layout = QHBoxLayout()
        
        # CPU
        self.cpu_label = QLabel("CPU: --%")
        self.cpu_label.setFont(QFont("Segoe UI", 10))
        
        # RAM
        self.ram_label = QLabel("RAM: --%")
        self.ram_label.setFont(QFont("Segoe UI", 10))
        
        # GPU
        self.gpu_label = QLabel("GPU: --%")
        self.gpu_label.setFont(QFont("Segoe UI", 10))
        
        # Detecciones totales
        self.total_detections_label = QLabel("Detecciones: 0")
        self.total_detections_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.total_detections_label.setStyleSheet("color: #e74c3c;")
        
        # FPS promedio
        self.avg_fps_label = QLabel("FPS Promedio: 0.0")
        self.avg_fps_label.setFont(QFont("Segoe UI", 10))
        
        info_layout.addWidget(self.cpu_label)
        info_layout.addWidget(self.ram_label)
        info_layout.addWidget(self.gpu_label)
        info_layout.addWidget(self.avg_fps_label)
        info_layout.addStretch()
        info_layout.addWidget(self.total_detections_label)
        
        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)
        
        # ==========================================
        # BOTONES DE CONTROL
        # ==========================================
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Botón Volver al Menú (regresa a la configuración de cámaras)
        self.backButton = QPushButton("⬅ Volver al Menú")
        self.backButton.setMinimumHeight(45)
        self.backButton.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.backButton.setStyleSheet("""
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
        self.backButton.clicked.connect(self.go_back)

        # Botón Pausar/Reanudar
        self.pauseButton = QPushButton("⏸ Pausar Sistema")
        self.pauseButton.setMinimumHeight(45)
        self.pauseButton.setFont(QFont("Segoe UI", 10))
        self.pauseButton.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        self.pauseButton.clicked.connect(self.toggle_pause)
        
        # Botón Detener
        self.stopButton = QPushButton("⏹ Detener Sistema")
        self.stopButton.setMinimumHeight(45)
        self.stopButton.setFont(QFont("Segoe UI", 10))
        self.stopButton.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.stopButton.clicked.connect(self.stop_system)
        
        button_layout.addWidget(self.backButton)
        button_layout.addStretch()
        button_layout.addWidget(self.pauseButton)
        button_layout.addWidget(self.stopButton)
        
        main_layout.addLayout(button_layout)
        
        # ==========================================
        # CONFIGURACIÓN DE VENTANA
        # ==========================================
        self.setWindowTitle(f"Monitoreo Activo - {self.num_cameras} Cámara(s)")

        # Tamaño mínimo modesto y apertura MAXIMIZADA, para que TODAS las
        # cámaras sean visibles (las que no quepan quedan accesibles con el
        # scroll del grid). Antes la ventana se hacía más grande que la
        # pantalla y las cámaras de la última fila quedaban fuera de vista.
        self.setMinimumSize(900, 600)
        self.setWindowState(Qt.WindowMaximized)
    
    def create_camera_widget(self, camera_id, width, height):
        """Crear widget para una cámara individual"""
        group = QGroupBox(f"📹 Cámara {camera_id}")
        group.setFont(QFont("Segoe UI", 10, QFont.Bold))
        
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Video label
        video_label = QLabel()
        video_label.setFixedSize(width, height)
        video_label.setAlignment(Qt.AlignCenter)
        video_label.setStyleSheet("""
            QLabel {
                background-color: #2c3e50;
                border: 2px solid #34495e;
                border-radius: 5px;
                color: white;
            }
        """)
        video_label.setText("🎥\nConectando...")
        video_label.setFont(QFont("Segoe UI", 12))
        
        self.camera_labels[camera_id] = video_label
        layout.addWidget(video_label)
        
        # Panel de información compacto
        info_layout = QHBoxLayout()
        info_layout.setSpacing(5)
        
        # Status
        status_label = QLabel("⏳")
        status_label.setFont(QFont("Segoe UI", 8))
        status_label.setMaximumWidth(150)
        self.status_labels[camera_id] = status_label
        
        # FPS
        fps_label = QLabel("FPS: 0")
        fps_label.setFont(QFont("Segoe UI", 8))
        fps_label.setMaximumWidth(60)
        self.fps_labels[camera_id] = fps_label
        
        # Detecciones
        detection_label = QLabel("Det: 0")
        detection_label.setFont(QFont("Segoe UI", 8, QFont.Bold))
        detection_label.setStyleSheet("color: #e74c3c;")
        detection_label.setMaximumWidth(60)
        self.detection_labels[camera_id] = detection_label
        
        info_layout.addWidget(status_label)
        info_layout.addStretch()
        info_layout.addWidget(fps_label)
        info_layout.addWidget(detection_label)
        
        layout.addLayout(info_layout)
        
        group.setLayout(layout)
        return group
    
    def start_detections(self):
        """Iniciar todos los threads de detección"""
        for cam_id, detection in self.detection_threads.items():
            # Conectar señales
            detection.changePixmap.connect(
                lambda img, cid=cam_id: self.update_camera_image(cid, img)
            )
            detection.statusUpdate.connect(
                lambda msg, cid=cam_id: self.update_camera_status(cid, msg)
            )
            detection.resourceUpdate.connect(self.update_system_resources)
            detection.weaponDetected.connect(self.on_weapon_detected)
            detection.error.connect(self.on_error)
            
            # Iniciar thread
            detection.start()
            
            logging.info(f"Thread de detección iniciado para cámara {cam_id}")
    
    def update_camera_image(self, camera_id, image):
        """Actualizar imagen de cámara"""
        if camera_id in self.camera_labels:
            self.camera_labels[camera_id].setPixmap(QPixmap.fromImage(image))
    
    def update_camera_status(self, camera_id, message):
        """Actualizar estado de cámara"""
        if camera_id in self.status_labels:
            # Extraer solo texto relevante (quitar [Cámara N])
            clean_msg = message.split(']')[-1].strip() if ']' in message else message
            self.status_labels[camera_id].setText(clean_msg[:20])
        
        # Actualizar FPS si viene en el mensaje
        if "FPS" in message and camera_id in self.fps_labels:
            try:
                fps = message.split("FPS")[0].split()[-1]
                self.fps_labels[camera_id].setText(f"FPS: {fps}")
            except:
                pass
    
    def update_system_resources(self, data):
        """Actualizar información de recursos del sistema"""
        try:
            self.cpu_label.setText(f"CPU: {data.get('cpu', 0):.1f}%")
            self.ram_label.setText(f"RAM: {data.get('memory', 0):.1f}%")
            
            if 'gpu_load' in data:
                self.gpu_label.setText(f"GPU: {data.get('gpu_load', 0):.1f}%")
            else:
                self.gpu_label.setText("GPU: N/A")
        except Exception as e:
            logging.error(f"Error al actualizar recursos: {e}")
    
    def on_weapon_detected(self, message):
        """Manejar detección de armas"""
        logging.warning(f"DETECCIÓN: {message}")
        
        # Actualizar contador de detecciones
        try:
            current = self.total_detections_label.text()
            count = int(current.split(":")[-1].strip())
            self.total_detections_label.setText(f"Detecciones: {count + 1}")
            
            # Actualizar contador por cámara
            for cam_id in self.detection_threads.keys():
                if f"Cámara {cam_id}" in message:
                    if cam_id in self.detection_labels:
                        label = self.detection_labels[cam_id]
                        current_det = int(label.text().split(":")[-1].strip())
                        label.setText(f"Det: {current_det + 1}")
                    break
        except:
            pass
        
        # Mostrar notificación visual
        self.system_status.setText("● DETECCIÓN ACTIVA")
        self.system_status.setStyleSheet("color: #e74c3c;")
        
        # Volver a normal después de 2 segundos
        QTimer.singleShot(2000, lambda: self.system_status.setText("● SISTEMA ACTIVO"))
        QTimer.singleShot(2000, lambda: self.system_status.setStyleSheet("color: #27ae60;"))
    
    def on_error(self, error_message):
        """Manejar errores"""
        logging.error(f"ERROR: {error_message}")
        # No mostrar popup para evitar interrumpir monitoreo
        # QMessageBox.warning(self, "Error en Sistema", error_message)
    
    def update_metrics(self):
        """Actualizar métricas cada segundo"""
        # Calcular FPS promedio
        try:
            fps_values = []
            for label in self.fps_labels.values():
                try:
                    fps = float(label.text().split(":")[-1].strip())
                    fps_values.append(fps)
                except:
                    pass
            
            if fps_values:
                avg_fps = sum(fps_values) / len(fps_values)
                self.avg_fps_label.setText(f"FPS Promedio: {avg_fps:.1f}")
        except:
            pass
    
    def toggle_pause(self):
        """Pausar/Reanudar sistema"""
        if self.pauseButton.text() == "⏸ Pausar Sistema":
            self.pauseButton.setText("▶️ Reanudar Sistema")
            self.system_status.setText("● SISTEMA PAUSADO")
            self.system_status.setStyleSheet("color: #f39c12;")
        else:
            self.pauseButton.setText("⏸ Pausar Sistema")
            self.system_status.setText("● SISTEMA ACTIVO")
            self.system_status.setStyleSheet("color: #27ae60;")
    
    def _shutdown_and_emit(self):
        """Detener métricas y notificar para volver al menú (una sola vez).

        El detener los threads de detección y el regreso a la ventana de
        configuración los maneja main.py en on_detection_closed (conectado a
        la señal `closed`).
        """
        if self._is_closing:
            return
        self._is_closing = True
        self.metrics_timer.stop()
        self.closed.emit()

    def go_back(self):
        """Volver al menú de configuración (detiene el monitoreo actual)"""
        reply = QMessageBox.question(
            self, 'Volver al Menú',
            '¿Volver al menú de configuración?\n\nSe detendrá el monitoreo actual.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            logging.info("Volviendo al menú de configuración...")
            self._shutdown_and_emit()

    def stop_system(self):
        """Detener el monitoreo y volver al menú de configuración"""
        reply = QMessageBox.question(
            self, 'Detener Monitoreo',
            '¿Desea detener el monitoreo y volver al menú de configuración?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            logging.info("Deteniendo sistema...")
            self._shutdown_and_emit()
    
    def center_window(self):
        """Centrar ventana en pantalla"""
        from PyQt5.QtWidgets import QDesktopWidget
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move(
            int((screen.width() - size.width()) / 2),
            int((screen.height() - size.height()) / 2)
        )
    
    def closeEvent(self, event):
        """Manejar cierre de ventana (botón X)"""
        # Si ya estamos cerrando desde un botón, no volver a preguntar
        if self._is_closing:
            event.accept()
            return

        reply = QMessageBox.question(
            self, 'Cerrar Monitoreo',
            '¿Detener el monitoreo y volver al menú de configuración?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            logging.info("Cerrando monitoreo - Usuario confirmó")
            self._shutdown_and_emit()
            event.accept()
        else:
            event.ignore()