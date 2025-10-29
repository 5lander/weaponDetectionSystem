# -*- coding: utf-8 -*-
"""
detectionWindowDual.py - Ventana de visualización para 2 cámaras
Muestra ambas cámaras simultáneamente con métricas en tiempo real
"""

import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QLabel, QPushButton,
                             QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
                             QMessageBox, QFrame)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap
import logging


class DetectionWindowDual(QMainWindow):
    """
    Ventana optimizada para mostrar 2 cámaras simultáneamente
    con información de rendimiento y detecciones
    """
    
    # Señal para notificar cuando se cierra
    closed = pyqtSignal()
    
    def __init__(self, detection_threads):
        """
        Args:
            detection_threads: Dict {camera_id: DetectionTapo_instance}
        """
        super(DetectionWindowDual, self).__init__()
        
        self.detection_threads = detection_threads
        self.camera_labels = {}
        self.status_labels = {}
        self.fps_labels = {}
        self.detection_labels = {}
        
        self.setupUI()
        self.start_detections()
        
        # Timer para actualizar métricas
        self.metrics_timer = QTimer()
        self.metrics_timer.timeout.connect(self.update_metrics)
        self.metrics_timer.start(1000)  # Actualizar cada segundo
        
        logging.info(f"DetectionWindowDual iniciada con {len(detection_threads)} cámara(s)")
    
    def setupUI(self):
        """Configurar interfaz de usuario"""
        
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
        
        title = QLabel("🎥 Sistema de Monitoreo Multi-Cámara")
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
        # GRID DE CÁMARAS
        # ==========================================
        cameras_layout = QGridLayout()
        cameras_layout.setSpacing(15)
        
        # Determinar layout según número de cámaras
        num_cameras = len(self.detection_threads)
        
        if num_cameras == 1:
            # Una sola cámara - pantalla completa
            cam_id = list(self.detection_threads.keys())[0]
            cam_widget = self.create_camera_widget(cam_id)
            cameras_layout.addWidget(cam_widget, 0, 0, 1, 2)
        
        elif num_cameras == 2:
            # Dos cámaras - lado a lado
            for idx, cam_id in enumerate(sorted(self.detection_threads.keys())):
                cam_widget = self.create_camera_widget(cam_id)
                cameras_layout.addWidget(cam_widget, 0, idx)
        
        main_layout.addLayout(cameras_layout)
        
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
        
        # GPU (si disponible)
        self.gpu_label = QLabel("GPU: --%")
        self.gpu_label.setFont(QFont("Segoe UI", 10))
        
        # Detecciones totales
        self.total_detections_label = QLabel("Detecciones: 0")
        self.total_detections_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.total_detections_label.setStyleSheet("color: #e74c3c;")
        
        info_layout.addWidget(self.cpu_label)
        info_layout.addWidget(self.ram_label)
        info_layout.addWidget(self.gpu_label)
        info_layout.addStretch()
        info_layout.addWidget(self.total_detections_label)
        
        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)
        
        # ==========================================
        # BOTONES DE CONTROL
        # ==========================================
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
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
        
        button_layout.addStretch()
        button_layout.addWidget(self.pauseButton)
        button_layout.addWidget(self.stopButton)
        
        main_layout.addLayout(button_layout)
        
        # Configuración de ventana
        self.setWindowTitle("Monitoreo Activo - Weapon Detection System")
        self.setMinimumSize(1400, 850)
        
        # Centrar en pantalla
        self.center_window()
    
    def create_camera_widget(self, camera_id):
        """Crear widget para una cámara individual"""
        group = QGroupBox(f"📹 Cámara {camera_id}")
        group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Video label
        video_label = QLabel()
        video_label.setMinimumSize(640, 480)
        video_label.setMaximumSize(800, 600)
        video_label.setAlignment(Qt.AlignCenter)
        video_label.setStyleSheet("""
            QLabel {
                background-color: #2c3e50;
                border: 2px solid #34495e;
                border-radius: 5px;
            }
        """)
        video_label.setText("🎥\nConectando...")
        video_label.setFont(QFont("Segoe UI", 14))
        video_label.setStyleSheet(video_label.styleSheet() + "color: white;")
        
        self.camera_labels[camera_id] = video_label
        layout.addWidget(video_label)
        
        # Panel de información de cámara
        info_layout = QHBoxLayout()
        
        # Status
        status_label = QLabel("Estado: Iniciando...")
        status_label.setFont(QFont("Segoe UI", 9))
        self.status_labels[camera_id] = status_label
        
        # FPS
        fps_label = QLabel("FPS: 0.0")
        fps_label.setFont(QFont("Segoe UI", 9))
        self.fps_labels[camera_id] = fps_label
        
        # Detecciones
        detection_label = QLabel("Detecciones: 0")
        detection_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        detection_label.setStyleSheet("color: #e74c3c;")
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
            self.status_labels[camera_id].setText(message)
        
        # Actualizar FPS si viene en el mensaje
        if "FPS" in message:
            try:
                fps = message.split("FPS")[0].split()[-1]
                if camera_id in self.fps_labels:
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
        QMessageBox.warning(self, "Error en Sistema", error_message)
    
    def update_metrics(self):
        """Actualizar métricas cada segundo"""
        # Esta función se ejecuta periódicamente
        # Aquí puedes agregar lógica adicional si necesitas
        pass
    
    def toggle_pause(self):
        """Pausar/Reanudar sistema"""
        # Implementar lógica de pausa si necesario
        if self.pauseButton.text() == "⏸ Pausar Sistema":
            self.pauseButton.setText("▶️ Reanudar Sistema")
            self.system_status.setText("● SISTEMA PAUSADO")
            self.system_status.setStyleSheet("color: #f39c12;")
        else:
            self.pauseButton.setText("⏸ Pausar Sistema")
            self.system_status.setText("● SISTEMA ACTIVO")
            self.system_status.setStyleSheet("color: #27ae60;")
    
    def stop_system(self):
        """Detener sistema completo"""
        reply = QMessageBox.question(
            self, 'Confirmar',
            '¿Desea detener el sistema de monitoreo?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            logging.info("Deteniendo sistema...")
            
            # Detener todos los threads
            for detection in self.detection_threads.values():
                detection.stop()
                detection.wait(5000)  # Esperar máximo 5 segundos
            
            self.metrics_timer.stop()
            
            # Emitir señal antes de cerrar
            self.closed.emit()
            
            self.close()
            
            logging.info("Sistema detenido correctamente")
    
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
        """Manejar cierre de ventana"""
        reply = QMessageBox.question(
            self, 'Confirmar Cierre',
            '¿Está seguro de cerrar el sistema?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            logging.info("Cerrando sistema de detección - Usuario confirmó")
            
            # Detener threads
            for detection in self.detection_threads.values():
                detection.stop()
            
            self.metrics_timer.stop()
            
            # Emitir señal de cierre
            self.closed.emit()
            
            event.accept()
        else:
            event.ignore()