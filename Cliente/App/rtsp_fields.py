# -*- coding: utf-8 -*-
"""
rtsp_fields.py - Grupo de campos RTSP reutilizable (marca, IP, puerto, usuario,
contraseña, canal, calidad y ruta personalizada) con vista previa en vivo de la URL.

Se usa tanto en el gestor de cámaras (AddCameraDialog) como en la ventana de
monitoreo (tabs por cámara), para que la lógica marca->ruta->preview exista en un
solo lugar.
"""

from PyQt5.QtWidgets import (QGroupBox, QLabel, QLineEdit, QComboBox, QCheckBox,
                             QFormLayout, QHBoxLayout, QWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from . import rtsp_profiles as profiles


class RtspFieldsGroup(QGroupBox):
    """QGroupBox con todos los campos de conexión RTSP de una cámara."""

    def __init__(self, parent=None, title="🌐 Conexión de la cámara"):
        super().__init__(title, parent)
        self.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self._rows = {}
        self._build()
        self._on_brand_changed()  # estado inicial de visibilidad + preview

    # ------------------------------------------------------------------ UI
    def _build(self):
        form = QFormLayout()
        form.setSpacing(12)
        form.setContentsMargins(18, 18, 18, 18)
        field_font = QFont("Segoe UI", 10)

        # --- Marca ---
        self.brand_combo = QComboBox()
        for _key, label in profiles.BRANDS:
            self.brand_combo.addItem(label)
        self.brand_combo.setFont(field_font)
        self.brand_combo.setMinimumHeight(38)
        self.brand_combo.currentIndexChanged.connect(self._on_brand_changed)
        self._add_row(form, 'brand', "📷 Marca/Tipo:", self.brand_combo)

        # --- IP ---
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("192.168.1.64")
        self.ip_input.setFont(field_font)
        self.ip_input.setMinimumHeight(38)
        self.ip_input.textChanged.connect(self._refresh_preview)
        self._add_row(form, 'ip', "🌐 Dirección IP:", self.ip_input)

        # --- Puerto ---
        self.port_input = QLineEdit()
        self.port_input.setText(str(profiles.DEFAULT_PORT))
        self.port_input.setPlaceholderText("554")
        self.port_input.setFont(field_font)
        self.port_input.setMinimumHeight(38)
        self.port_input.textChanged.connect(self._refresh_preview)
        self._add_row(form, 'port', "🔌 Puerto:", self.port_input)

        # --- Usuario ---
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("admin")
        self.user_input.setFont(field_font)
        self.user_input.setMinimumHeight(38)
        self.user_input.textChanged.connect(self._refresh_preview)
        self._add_row(form, 'username', "👤 Usuario:", self.user_input)

        # --- Contraseña (+ mostrar) ---
        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Contraseña")
        self.pass_input.setFont(field_font)
        self.pass_input.setMinimumHeight(38)
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.textChanged.connect(self._refresh_preview)
        show_pass = QCheckBox("Mostrar")
        show_pass.setFont(QFont("Segoe UI", 9))
        show_pass.stateChanged.connect(
            lambda state: self.pass_input.setEchoMode(
                QLineEdit.Normal if state == Qt.Checked else QLineEdit.Password
            )
        )
        pass_container = QWidget()
        pass_layout = QHBoxLayout(pass_container)
        pass_layout.setContentsMargins(0, 0, 0, 0)
        pass_layout.addWidget(self.pass_input)
        pass_layout.addWidget(show_pass)
        self._add_row(form, 'password', "🔒 Contraseña:", pass_container)

        # --- Canal (solo marcas con NVR) ---
        self.channel_input = QLineEdit()
        self.channel_input.setText("1")
        self.channel_input.setPlaceholderText("1")
        self.channel_input.setFont(field_font)
        self.channel_input.setMinimumHeight(38)
        self.channel_input.textChanged.connect(self._refresh_preview)
        self._add_row(form, 'channel', "🔢 Canal (NVR):", self.channel_input)

        # --- Calidad ---
        self.quality_combo = QComboBox()
        for _key, label in profiles.QUALITIES:
            self.quality_combo.addItem(label)
        self.quality_combo.setFont(field_font)
        self.quality_combo.setMinimumHeight(38)
        self.quality_combo.currentIndexChanged.connect(self._refresh_preview)
        self._add_row(form, 'quality', "📺 Calidad:", self.quality_combo)

        # --- Ruta personalizada (solo marca genérica/otra) ---
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Streaming/Channels/101  (o pega la URL rtsp:// completa)")
        self.path_input.setFont(field_font)
        self.path_input.setMinimumHeight(38)
        self.path_input.textChanged.connect(self._refresh_preview)
        self._add_row(form, 'path', "🛣️ Ruta RTSP:", self.path_input)

        # --- Vista previa de la URL ---
        self.preview_label = QLabel("rtsp://…")
        self.preview_label.setFont(QFont("Consolas", 9))
        self.preview_label.setWordWrap(True)
        self.preview_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.preview_label.setStyleSheet(
            "color: #2c3e50; background-color: #ecf0f1; border: 1px solid #bdc3c7;"
            " border-radius: 4px; padding: 6px;"
        )
        self._add_row(form, 'preview', "🔗 URL resultante:", self.preview_label)

        self.setLayout(form)

    def _add_row(self, form, name, label_text, field):
        label = QLabel(label_text)
        label.setFont(QFont("Segoe UI", 10))
        form.addRow(label, field)
        self._rows[name] = (label, field)

    def _set_row_visible(self, name, visible):
        label, field = self._rows[name]
        label.setVisible(visible)
        field.setVisible(visible)

    # -------------------------------------------------------------- estado
    def current_brand(self):
        idx = self.brand_combo.currentIndex()
        if 0 <= idx < len(profiles.BRANDS):
            return profiles.BRANDS[idx][0]
        return profiles.DEFAULT_BRAND

    def _current_quality(self):
        idx = self.quality_combo.currentIndex()
        if 0 <= idx < len(profiles.QUALITIES):
            return profiles.QUALITIES[idx][0]
        return 'main'

    def _on_brand_changed(self):
        brand = self.current_brand()
        self._set_row_visible('channel', profiles.brand_needs_channel(brand))
        self._set_row_visible('path', profiles.brand_uses_custom_path(brand))
        self._refresh_preview()

    def _refresh_preview(self):
        try:
            self.preview_label.setText(profiles.masked_rtsp_url(self.get_config()))
        except Exception:
            self.preview_label.setText("rtsp://…")

    # ----------------------------------------------------------- get/set
    def get_config(self):
        """Devolver la config (dict) representada por los campos."""
        try:
            port = int(self.port_input.text().strip())
        except (ValueError, AttributeError):
            port = profiles.DEFAULT_PORT
        try:
            channel = int(self.channel_input.text().strip())
        except (ValueError, AttributeError):
            channel = 1

        quality = self._current_quality()
        return {
            'brand': self.current_brand(),
            'ip': self.ip_input.text().strip(),
            'port': port,
            'username': self.user_input.text().strip(),
            'password': self.pass_input.text(),
            'channel': channel,
            'quality': quality,
            'stream': profiles.quality_to_stream(quality),  # compat legacy
            'path': self.path_input.text().strip(),
        }

    def set_config(self, cfg):
        """Cargar valores desde una config existente (con compat de formato viejo)."""
        cfg = cfg or {}

        # Marca
        brand = (cfg.get('brand') or profiles.DEFAULT_BRAND).lower()
        brand_idx = next((i for i, (k, _l) in enumerate(profiles.BRANDS) if k == brand), 0)
        self.brand_combo.setCurrentIndex(brand_idx)

        self.ip_input.setText(str(cfg.get('ip', '') or ''))
        self.port_input.setText(str(cfg.get('port', profiles.DEFAULT_PORT) or profiles.DEFAULT_PORT))
        self.user_input.setText(str(cfg.get('username', '') or ''))
        self.pass_input.setText(str(cfg.get('password', '') or ''))
        self.channel_input.setText(str(cfg.get('channel', 1) or 1))
        self.path_input.setText(str(cfg.get('path', '') or ''))

        quality = profiles.normalize_quality(cfg)
        self.quality_combo.setCurrentIndex(1 if quality == 'sub' else 0)

        self._on_brand_changed()

    def rtsp_url(self):
        """URL RTSP completa (con contraseña real) para probar/conectar."""
        return profiles.build_rtsp_url(self.get_config())
