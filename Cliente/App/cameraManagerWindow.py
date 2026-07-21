# -*- coding: utf-8 -*-
"""
cameraManagerWindow.py - GESTOR DE CÁMARAS INTUITIVO
Agrega, edita y elimina cámaras desde la interfaz gráfica
"""

import json
import os
from PyQt5.QtWidgets import (QDialog, QWidget, QLabel, QLineEdit, 
                             QPushButton, QCheckBox, QGroupBox,
                             QVBoxLayout, QHBoxLayout, QFormLayout, QMessageBox,
                             QListWidget, QListWidgetItem, QDialogButtonBox, QFileDialog)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
import logging
import cv2

from .rtsp_fields import RtspFieldsGroup
from . import rtsp_profiles as profiles


class AddCameraDialog(QDialog):
    """Diálogo para agregar/editar una cámara"""
    
    def __init__(self, parent=None, camera_data=None, is_edit=False):
        super().__init__(parent)
        self.camera_data = camera_data or {}
        self.is_edit = is_edit
        
        self.setWindowTitle("✏️ Editar Cámara" if is_edit else "➕ Agregar Nueva Cámara")
        self.setMinimumWidth(580)
        
        self.setupUI()
        
        if camera_data:
            self.load_camera_data()
    
    def setupUI(self):
        """Configurar interfaz del diálogo"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Título
        title = QLabel("➕ Nueva Cámara" if not self.is_edit else "✏️ Editar Cámara")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Identificación (nombre + ubicación + estado)
        form_group = QGroupBox("📋 Información de la Cámara")
        form_group.setFont(QFont("Segoe UI", 10, QFont.Bold))
        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        # Nombre
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Cámara Entrada Principal")
        self.name_input.setMinimumHeight(35)
        form_layout.addRow("🏷️ Nombre:", self.name_input)

        # Ubicación
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Ej: Entrada Principal, Piso 2")
        self.location_input.setMinimumHeight(35)
        form_layout.addRow("📍 Ubicación:", self.location_input)

        # Habilitada
        self.enabled_check = QCheckBox("Habilitar esta cámara")
        self.enabled_check.setChecked(True)
        self.enabled_check.setFont(QFont("Segoe UI", 10))
        form_layout.addRow("✅ Estado:", self.enabled_check)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # Conexión RTSP (marca, IP, puerto, usuario, contraseña, canal, calidad, ruta)
        self.fields = RtspFieldsGroup(self)
        layout.addWidget(self.fields)

        # Botón de prueba
        test_btn = QPushButton("🔧 Probar Conexión")
        test_btn.setMinimumHeight(40)
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        test_btn.clicked.connect(self.test_connection)
        layout.addWidget(test_btn)
        
        # Botones de acción
        button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        button_box.button(QDialogButtonBox.Save).setText("💾 Guardar")
        button_box.button(QDialogButtonBox.Cancel).setText("❌ Cancelar")
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def load_camera_data(self):
        """Cargar datos de cámara existente"""
        self.name_input.setText(self.camera_data.get('name', ''))
        self.location_input.setText(self.camera_data.get('location', ''))
        self.enabled_check.setChecked(self.camera_data.get('enabled', True))
        self.fields.set_config(self.camera_data)

    def test_connection(self):
        """Probar conexión con los datos ingresados"""
        cfg = self.fields.get_config()
        ip = cfg['ip']
        user = cfg['username']
        password = cfg['password']

        if not ip or not user or not password:
            QMessageBox.warning(
                self, "Campos Incompletos",
                "Complete IP, usuario y contraseña para probar."
            )
            return

        rtsp_url = self.fields.rtsp_url()

        try:
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
                "rtsp_transport;udp|fflags;nobuffer|flags;low_delay"
            )
            
            cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
            
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    
                    QMessageBox.information(
                        self, "✅ Conexión Exitosa",
                        f"¡Cámara conectada correctamente!\n\n"
                        f"Resolución: {width}x{height}\n"
                        f"IP: {ip}\n"
                        f"Marca: {profiles.brand_label(cfg['brand'])}"
                    )
                else:
                    QMessageBox.warning(
                        self, "⚠️ Advertencia",
                        "Conectó pero no se pudieron leer frames."
                    )
                cap.release()
            else:
                QMessageBox.critical(
                    self, "❌ Error de Conexión",
                    "No se pudo conectar a la cámara.\n\n"
                    "Verificar:\n"
                    "• IP correcta\n"
                    "• Credenciales correctas\n"
                    "• Cámara encendida\n"
                    "• Misma red WiFi"
                )
        
        except Exception as e:
            QMessageBox.critical(
                self, "Error",
                f"Error al probar conexión:\n{str(e)}"
            )
    
    def validate_and_accept(self):
        """Validar datos antes de aceptar"""
        cfg = self.fields.get_config()

        if not self.name_input.text():
            QMessageBox.warning(self, "Campo Requerido", "Ingrese un nombre para la cámara.")
            return

        if not self.location_input.text():
            QMessageBox.warning(self, "Campo Requerido", "Ingrese la ubicación.")
            return

        if profiles.brand_uses_custom_path(cfg['brand']):
            # Marca genérica: basta con una ruta/URL RTSP (puede traer su propia IP/credenciales).
            if not cfg['path']:
                QMessageBox.warning(self, "Campo Requerido",
                                    "Ingrese la ruta RTSP (o pegue la URL rtsp:// completa).")
                return
            if not str(cfg['path']).lower().startswith('rtsp://') and not cfg['ip']:
                QMessageBox.warning(self, "Campo Requerido", "Ingrese la dirección IP.")
                return
        else:
            if not cfg['ip']:
                QMessageBox.warning(self, "Campo Requerido", "Ingrese la dirección IP.")
                return
            if not cfg['username']:
                QMessageBox.warning(self, "Campo Requerido", "Ingrese el usuario.")
                return
            if not cfg['password']:
                QMessageBox.warning(self, "Campo Requerido", "Ingrese la contraseña.")
                return

        self.accept()

    def get_camera_data(self):
        """Obtener datos de la cámara (identificación + conexión RTSP)."""
        data = {
            'name': self.name_input.text(),
            'location': self.location_input.text(),
            'enabled': self.enabled_check.isChecked(),
        }
        data.update(self.fields.get_config())
        return data


class CameraManagerWindow(QDialog):
    """
    Ventana de diálogo para gestionar cámaras
    Permite agregar, editar, eliminar y probar cámaras
    """
    camerasUpdated = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_file = 'cameras.json'
        self.cameras = self.load_cameras()
        
        self.setupUI()
        self.update_camera_list()
        
        logging.info("CameraManagerWindow inicializada")
    
    def setupUI(self):
        """Configurar interfaz principal"""
        self.setWindowTitle("🎥 Gestor de Cámaras")
        self.setMinimumSize(900, 600)
        self.setModal(True)
        
        # Layout principal directo (QDialog no usa setCentralWidget)
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # ==========================================
        # PANEL IZQUIERDO - LISTA DE CÁMARAS
        # ==========================================
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(10)
        
        # Título
        title = QLabel("📹 Cámaras Configuradas")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        left_layout.addWidget(title)
        
        # Contador
        self.count_label = QLabel(f"Total: {len(self.cameras)} cámara(s)")
        self.count_label.setFont(QFont("Segoe UI", 10))
        self.count_label.setStyleSheet("color: #7f8c8d;")
        left_layout.addWidget(self.count_label)
        
        # Lista de cámaras
        self.camera_list = QListWidget()
        self.camera_list.setFont(QFont("Segoe UI", 10))
        self.camera_list.setAlternatingRowColors(True)
        self.camera_list.itemSelectionChanged.connect(self.on_camera_selected)
        left_layout.addWidget(self.camera_list)
        
        # Botones de lista
        list_buttons = QHBoxLayout()
        
        add_btn = QPushButton("➕ Agregar")
        add_btn.setMinimumHeight(40)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        add_btn.clicked.connect(self.add_camera)
        
        edit_btn = QPushButton("✏️ Editar")
        edit_btn.setMinimumHeight(40)
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        edit_btn.clicked.connect(self.edit_camera)
        
        delete_btn = QPushButton("🗑️ Eliminar")
        delete_btn.setMinimumHeight(40)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        delete_btn.clicked.connect(self.delete_camera)
        
        list_buttons.addWidget(add_btn)
        list_buttons.addWidget(edit_btn)
        list_buttons.addWidget(delete_btn)
        left_layout.addLayout(list_buttons)
        
        main_layout.addWidget(left_panel, 1)
        
        # ==========================================
        # PANEL DERECHO - DETALLES
        # ==========================================
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(15)
        
        # Título
        details_title = QLabel("📋 Detalles de la Cámara")
        details_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        right_layout.addWidget(details_title)
        
        # Group box de detalles
        self.details_group = QGroupBox("Información")
        self.details_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        details_layout = QFormLayout()
        details_layout.setSpacing(12)
        
        self.detail_name = QLabel("---")
        self.detail_brand = QLabel("---")
        self.detail_ip = QLabel("---")
        self.detail_user = QLabel("---")
        self.detail_location = QLabel("---")
        self.detail_stream = QLabel("---")
        self.detail_status = QLabel("---")

        for label in [self.detail_name, self.detail_brand, self.detail_ip, self.detail_user,
                      self.detail_location, self.detail_stream, self.detail_status]:
            label.setFont(QFont("Segoe UI", 10))
            label.setWordWrap(True)

        details_layout.addRow("🏷️ Nombre:", self.detail_name)
        details_layout.addRow("📷 Marca:", self.detail_brand)
        details_layout.addRow("🌐 IP:", self.detail_ip)
        details_layout.addRow("👤 Usuario:", self.detail_user)
        details_layout.addRow("📍 Ubicación:", self.detail_location)
        details_layout.addRow("📺 Calidad:", self.detail_stream)
        details_layout.addRow("✅ Estado:", self.detail_status)
        
        self.details_group.setLayout(details_layout)
        right_layout.addWidget(self.details_group)
        
        # Botones de acción
        action_buttons = QVBoxLayout()
        action_buttons.setSpacing(10)
        
        test_btn = QPushButton("🔧 Probar Conexión")
        test_btn.setMinimumHeight(45)
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        test_btn.clicked.connect(self.test_selected_camera)
        
        export_btn = QPushButton("📤 Exportar Configuración")
        export_btn.setMinimumHeight(45)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        export_btn.clicked.connect(self.export_config)
        
        import_btn = QPushButton("📥 Importar Configuración")
        import_btn.setMinimumHeight(45)
        import_btn.setStyleSheet("""
            QPushButton {
                background-color: #16a085;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138d75;
            }
        """)
        import_btn.clicked.connect(self.import_config)
        
        action_buttons.addWidget(test_btn)
        action_buttons.addWidget(export_btn)
        action_buttons.addWidget(import_btn)
        action_buttons.addStretch()
        
        right_layout.addLayout(action_buttons)
        
        # Botón cerrar
        close_btn = QPushButton("✅ Guardar y Cerrar")
        close_btn.setMinimumHeight(50)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        close_btn.clicked.connect(self.save_and_close)
        right_layout.addWidget(close_btn)
        
        main_layout.addWidget(right_panel, 1)
        
        # Centrar ventana
        self.center_window()
    
    def load_cameras(self):
        """Cargar cámaras desde JSON"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                logging.error("Error al cargar cameras.json")
                return {}
        return {}
    
    def save_cameras(self):
        """Guardar cámaras a JSON"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.cameras, f, indent=4, ensure_ascii=False)
            logging.info("Configuración guardada en cameras.json")
            return True
        except Exception as e:
            logging.error(f"Error al guardar: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo guardar:\n{str(e)}")
            return False
    
    def update_camera_list(self):
        """Actualizar lista de cámaras"""
        self.camera_list.clear()
        
        for key in sorted(self.cameras.keys(), key=lambda x: int(x.split('_')[1])):
            cam = self.cameras[key]
            enabled = "✅" if cam.get('enabled', True) else "⚪"
            item_text = f"{enabled} {cam.get('name', 'Sin nombre')} - {cam.get('ip', 'Sin IP')}"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, key)
            self.camera_list.addItem(item)
        
        self.count_label.setText(f"Total: {len(self.cameras)} cámara(s)")
    
    def on_camera_selected(self):
        """Cuando se selecciona una cámara"""
        items = self.camera_list.selectedItems()
        if not items:
            return
        
        key = items[0].data(Qt.UserRole)
        cam = self.cameras[key]
        
        self.detail_name.setText(cam.get('name', '---'))
        self.detail_brand.setText(profiles.brand_label(cam.get('brand', 'tapo')))
        self.detail_ip.setText(cam.get('ip', '---'))
        self.detail_user.setText(cam.get('username', '---'))
        self.detail_location.setText(cam.get('location', '---'))

        quality = profiles.normalize_quality(cam)
        self.detail_stream.setText(
            "Principal (alta calidad)" if quality == 'main' else "Secundaria (baja calidad)"
        )

        enabled = cam.get('enabled', True)
        self.detail_status.setText("✅ Habilitada" if enabled else "⚪ Deshabilitada")
    
    def add_camera(self):
        """Agregar nueva cámara"""
        dialog = AddCameraDialog(self)
        
        if dialog.exec_() == QDialog.Accepted:
            # Encontrar próximo número
            existing_nums = [int(k.split('_')[1]) for k in self.cameras.keys()]
            next_num = max(existing_nums) + 1 if existing_nums else 1
            
            key = f'camera_{next_num}'
            self.cameras[key] = dialog.get_camera_data()
            
            self.save_cameras()
            self.update_camera_list()
            
            QMessageBox.information(
                self, "✅ Éxito",
                f"Cámara {next_num} agregada correctamente."
            )
    
    def edit_camera(self):
        """Editar cámara seleccionada"""
        items = self.camera_list.selectedItems()
        if not items:
            QMessageBox.warning(self, "Sin Selección", "Seleccione una cámara para editar.")
            return
        
        key = items[0].data(Qt.UserRole)
        camera_data = self.cameras[key]
        
        dialog = AddCameraDialog(self, camera_data, is_edit=True)
        
        if dialog.exec_() == QDialog.Accepted:
            self.cameras[key] = dialog.get_camera_data()
            self.save_cameras()
            self.update_camera_list()
            
            QMessageBox.information(self, "✅ Éxito", "Cámara actualizada correctamente.")
    
    def delete_camera(self):
        """Eliminar cámara seleccionada"""
        items = self.camera_list.selectedItems()
        if not items:
            QMessageBox.warning(self, "Sin Selección", "Seleccione una cámara para eliminar.")
            return
        
        key = items[0].data(Qt.UserRole)
        cam = self.cameras[key]
        
        reply = QMessageBox.question(
            self, 'Confirmar Eliminación',
            f"¿Eliminar la cámara '{cam.get('name', 'Sin nombre')}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            del self.cameras[key]
            self.save_cameras()
            self.update_camera_list()
            
            # Limpiar detalles
            for label in [self.detail_name, self.detail_brand, self.detail_ip, self.detail_user,
                          self.detail_location, self.detail_stream, self.detail_status]:
                label.setText("---")
    
    def test_selected_camera(self):
        """Probar cámara seleccionada"""
        items = self.camera_list.selectedItems()
        if not items:
            QMessageBox.warning(self, "Sin Selección", "Seleccione una cámara para probar.")
            return
        
        key = items[0].data(Qt.UserRole)
        cam = self.cameras[key]

        ip = cam.get('ip')
        rtsp_url = profiles.build_rtsp_url(cam)

        try:
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
                "rtsp_transport;udp|fflags;nobuffer|flags;low_delay"
            )

            cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
            
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    
                    QMessageBox.information(
                        self, "✅ Conexión Exitosa",
                        f"¡Cámara conectada!\n\n"
                        f"Resolución: {width}x{height}\n"
                        f"IP: {ip}"
                    )
                else:
                    QMessageBox.warning(self, "⚠️ Advertencia", "Conectó pero sin frames.")
                cap.release()
            else:
                QMessageBox.critical(self, "❌ Error", "No se pudo conectar.")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error:\n{str(e)}")
    
    def export_config(self):
        """Exportar configuración a archivo"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Exportar Configuración",
            "cameras_backup.json",
            "JSON Files (*.json)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.cameras, f, indent=4, ensure_ascii=False)
                QMessageBox.information(self, "✅ Exportado", f"Guardado en:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo exportar:\n{str(e)}")
    
    def import_config(self):
        """Importar configuración desde archivo"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Importar Configuración",
            "",
            "JSON Files (*.json)"
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    imported = json.load(f)
                
                reply = QMessageBox.question(
                    self, 'Confirmar',
                    f"¿Importar {len(imported)} cámara(s)?\n"
                    "Esto reemplazará la configuración actual.",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    self.cameras = imported
                    self.save_cameras()
                    self.update_camera_list()
                    QMessageBox.information(self, "✅ Importado", "Configuración importada.")
            
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo importar:\n{str(e)}")
    
    def save_and_close(self):
        """Guardar y cerrar"""
        if self.save_cameras():
            self.camerasUpdated.emit()
            self.accept()
    
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
        """Al cerrar la ventana"""
        self.save_cameras()
        self.camerasUpdated.emit()
        event.accept()