# detectionWindowStyle.py - Archivo de estilos para la ventana de detección

class DetectionWindowStyles:
    """Clase que contiene todos los estilos para la ventana de detección"""
    
    # Estilo general de la ventana principal
    MAIN_WINDOW = """
        QMainWindow {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 #0f172a, stop: 1 #1e293b);
            border: 2px solid #334155;
            border-radius: 12px;
        }
    """
    
    # Estilo del label de la cámara
    CAMERA_LABEL = """
        QLabel {
            background: #1e293b;
            border: 3px solid #475569;
            border-radius: 15px;
            padding: 10px;
        }
        QLabel:hover {
            border-color: #64748b;
        }
    """
    
    # Estilo del botón de parar
    STOP_BUTTON = """
        QPushButton {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 #ef4444, stop: 1 #dc2626);
            color: white;
            border: none;
            border-radius: 12px;
            font-weight: 700;
            font-size: 14px;
            font-family: 'Segoe UI', Arial, sans-serif;
            padding: 8px 16px;
        }
        QPushButton:hover {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 #f87171, stop: 1 #ef4444);
        }
        QPushButton:pressed {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 #dc2626, stop: 1 #b91c1c);
        }
        QPushButton:disabled {
            background: #6b7280;
            color: #9ca3af;
        }
    """
    
    # Estilo del botón de volver
    BACK_BUTTON = """
        QPushButton {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 #6b7280, stop: 1 #4b5563);
            color: white;
            border: none;
            border-radius: 12px;
            font-weight: 600;
            font-size: 14px;
            font-family: 'Segoe UI', Arial, sans-serif;
            padding: 8px 16px;
        }
        QPushButton:hover {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 #9ca3af, stop: 1 #6b7280);
        }
        QPushButton:pressed {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 #4b5563, stop: 1 #374151);
        }
        QPushButton:disabled {
            background: #374151;
            color: #6b7280;
        }
    """
    
    # Estilo del frame de recursos del sistema
    SYSTEM_RESOURCES_FRAME = """
        QFrame {
            background: rgba(30, 41, 59, 0.95);
            border-radius: 15px;
            border: 2px solid #475569;
            padding: 10px;
        }
    """
    
    # Estilo de las etiquetas de recursos
    RESOURCE_LABEL = """
        QLabel {
            color: #e2e8f0;
            font-family: 'Consolas', 'Monaco', monospace;
            font-weight: 600;
            font-size: 12px;
            background: transparent;
            border: none;
            padding: 3px 8px;
        }
    """
    
    # Estilo específico para CPU
    CPU_LABEL = """
        QLabel {
            color: #10b981;
            font-family: 'Consolas', 'Monaco', monospace;
            font-weight: 600;
            font-size: 11px;
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid #10b981;
            border-radius: 8px;
            padding: 8px 12px;
        }
    """
    
    # Estilo específico para Memoria
    MEMORY_LABEL = """
        QLabel {
            color: #3b82f6;
            font-family: 'Consolas', 'Monaco', monospace;
            font-weight: 600;
            font-size: 11px;
            background: rgba(59, 130, 246, 0.1);
            border: 1px solid #3b82f6;
            border-radius: 8px;
            padding: 8px 12px;
        }
    """
    
    # Estilo específico para GPU
    GPU_LABEL = """
        QLabel {
            color: #f59e0b;
            font-family: 'Consolas', 'Monaco', monospace;
            font-weight: 600;
            font-size: 11px;
            background: rgba(245, 158, 11, 0.1);
            border: 1px solid #f59e0b;
            border-radius: 8px;
            padding: 8px 12px;
        }
    """
    
    # Estilo del frame de información de detección
    DETECTION_INFO_FRAME = """
        QFrame {
            background: rgba(15, 23, 42, 0.95);
            border-radius: 12px;
            border: 2px solid #1e40af;
            padding: 8px;
        }
    """
    
    # Estilo para labels de información de detección
    DETECTION_INFO_LABEL = """
        QLabel {
            color: #60a5fa;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-weight: 600;
            font-size: 11px;
            background: transparent;
            border: none;
            padding: 2px 6px;
        }
    """
    
    # Estilo para indicador de estado de detección
    DETECTION_STATUS_ACTIVE = """
        QLabel {
            background: #10b981;
            border-radius: 8px;
            color: white;
            font-weight: bold;
            padding: 4px 12px;
            font-size: 11px;
        }
    """
    
    DETECTION_STATUS_INACTIVE = """
        QLabel {
            background: #6b7280;
            border-radius: 8px;
            color: white;
            font-weight: bold;
            padding: 4px 12px;
            font-size: 11px;
        }
    """
    
    DETECTION_STATUS_ERROR = """
        QLabel {
            background: #ef4444;
            border-radius: 8px;
            color: white;
            font-weight: bold;
            padding: 4px 12px;
            font-size: 11px;
        }
    """
    
    # Estilo del título de la ventana
    TITLE_LABEL = """
        QLabel {
            color: #f1f5f9;
            font-size: 18px;
            font-weight: bold;
            font-family: 'Segoe UI', Arial, sans-serif;
            padding: 8px 12px;
            background: rgba(30, 41, 59, 0.8);
            border-radius: 10px;
            border: 1px solid #475569;
        }
    """
    
    # Estilo para barra de progreso de detección
    DETECTION_PROGRESS_BAR = """
        QProgressBar {
            border: none;
            border-radius: 6px;
            background: #374151;
            text-align: center;
            color: white;
            font-weight: bold;
            font-size: 11px;
        }
        QProgressBar::chunk {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 #10b981, stop: 1 #059669);
            border-radius: 6px;
        }
    """
    
    @staticmethod
    def get_alert_message_style(alert_type="warning"):
        """Genera el estilo para mensajes de alerta según el tipo"""
        colors = {
            "warning": {"bg": "#fbbf24", "text": "#92400e"},
            "danger": {"bg": "#ef4444", "text": "#ffffff"},
            "success": {"bg": "#10b981", "text": "#ffffff"},
            "info": {"bg": "#3b82f6", "text": "#ffffff"}
        }
        
        color_scheme = colors.get(alert_type, colors["warning"])
        
        return f"""
            QMessageBox {{
                background: #1e293b;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
                color: #e2e8f0;
                min-width: 400px;
                max-width: 600px;
                min-height: 200px;
                border-radius: 12px;
                border: 2px solid {color_scheme['bg']};
            }}
            QMessageBox QLabel {{
                color: #e2e8f0;
                font-size: 13px;
                padding: 15px;
                background: transparent;
            }}
            QMessageBox QPushButton {{
                background: {color_scheme['bg']};
                color: {color_scheme['text']};
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 13px;
                min-width: 100px;
                margin: 10px 5px;
            }}
            QMessageBox QPushButton:hover {{
                opacity: 0.8;
            }}
            QMessageBox QPushButton:pressed {{
                opacity: 0.6;
            }}
        """

class DetectionStatusStyles:
    """Estilos para indicadores de estado de detección"""
    
    COLORS = {
        "detecting": "#10b981",
        "monitoring": "#3b82f6", 
        "paused": "#f59e0b",
        "stopped": "#6b7280",
        "error": "#ef4444",
        "weapon_detected": "#ef4444"
    }
    
    @classmethod
    def get_status_style(cls, status):
        """Retorna el estilo para un estado específico de detección"""
        color = cls.COLORS.get(status, cls.COLORS["stopped"])
        return f"""
            QLabel {{
                background: {color};
                border-radius: 8px;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                font-size: 12px;
                border: 2px solid {color};
            }}
        """

class ResourceIndicatorStyles:
    """Estilos para indicadores de recursos del sistema"""
    
    @staticmethod
    def get_resource_style_by_level(resource_type, level):
        """Retorna el estilo según el nivel de uso del recurso"""
        if level < 50:
            color = "#10b981"  # Verde - Bajo uso
        elif level < 80:
            color = "#f59e0b"  # Amarillo - Uso medio
        else:
            color = "#ef4444"  # Rojo - Alto uso
            
        return f"""
            QLabel {{
                color: {color};
                font-family: 'Consolas', 'Monaco', monospace;
                font-weight: 600;
                font-size: 11px;
                background: rgba({','.join([str(int(color[i:i+2], 16)) for i in (1, 3, 5)])}, 0.1);
                border: 1px solid {color};
                border-radius: 8px;
                padding: 8px 12px;
            }}
        """