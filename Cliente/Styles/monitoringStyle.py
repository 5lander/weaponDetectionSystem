# monitoringStyle.py - Archivo de estilos para la ventana de monitoreo - CORREGIDO

class MonitoringWindowStyles:
    """Clase que contiene todos los estilos para la ventana de monitoreo"""
    
    # Estilo general de la ventana principal
    MAIN_WINDOW = """
        QMainWindow {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 #f1f5f9, stop: 1 #e2e8f0);
            border: 1px solid #cbd5e1;
        }
        QWidget#centralwidget {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 #f1f5f9, stop: 1 #e2e8f0);
        }
    """
    
    # Estilo del texto informativo
    INFO_TEXT = """
        QLabel {
            color: #1e293b;
            font-size: 13px;
            font-weight: 500;
            font-family: 'Segoe UI', Arial, sans-serif;
            padding: 20px;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            border: 1px solid #e2e8f0;
            line-height: 1.5;
        }
    """
    
    # Estilo para las etiquetas de los campos
    FIELD_LABEL = """
        QLabel {
            color: #374151;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-weight: 600;
            font-size: 13px;
            background: transparent;
            border: none;
            margin-bottom: 5px;
        }
    """
    
    # Estilo para campos de entrada - CORREGIDO
    INPUT_FIELD = """
        QLineEdit {
            background: white;
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            padding: 12px 18px;
            font-size: 14px;
            color: #1e293b;
            font-family: 'Segoe UI', Arial, sans-serif;
            min-height: 25px;
            max-height: 35px;
        }
        QLineEdit:focus {
            border-color: #3b82f6;
            outline: none;
        }
        QLineEdit:hover {
            border-color: #cbd5e1;
        }
        QLineEdit::placeholder {
            color: #94a3b8;
            font-style: italic;
        }
    """
    
    # Estilo para campo con error - CORREGIDO
    INPUT_FIELD_ERROR = """
        QLineEdit {
            background: white;
            border: 2px solid #fbbf24;
            border-radius: 10px;
            padding: 12px 16px;
            font-size: 14px;
            color: #374151;
            font-family: 'Segoe UI', Arial, sans-serif;
            min-height: 25px;
            max-height: 35px;
        }
        QLineEdit:focus {
            border-color: #f59e0b;
            outline: none;
        }
        QLineEdit:hover {
            border-color: #fbbf24;
        }
        QLineEdit::placeholder {
            color: #94a3b8;
            font-style: italic;
        }
    """
    
    # Estilo del botón de monitoreo (principal)
    MONITORING_BUTTON = """
        QPushButton {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 #10b981, stop: 1 #059669);
            color: white;
            border: none;
            border-radius: 10px;
            font-weight: 600;
            font-size: 14px;
            font-family: 'Segoe UI', Arial, sans-serif;
            padding: 12px 16px;
            min-height: 20px;
        }
        QPushButton:hover {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 #059669, stop: 1 #047857);
        }
        QPushButton:pressed {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 #047857, stop: 1 #065f46);
        }
        QPushButton:disabled {
            background: #9ca3af;
            color: #f3f4f6;
        }
    """
    
    # Estilo del botón de monitoreo cuando está activo
    MONITORING_BUTTON_ACTIVE = """
        QPushButton {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 #ef4444, stop: 1 #dc2626);
            color: white;
            border: none;
            border-radius: 10px;
            font-weight: 600;
            font-size: 14px;
            font-family: 'Segoe UI', Arial, sans-serif;
            padding: 12px 16px;
            min-height: 20px;
        }
        QPushButton:hover {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 #dc2626, stop: 1 #b91c1c);
        }
        QPushButton:pressed {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 #b91c1c, stop: 1 #991b1b);
        }
    """
    
    # Estilo del botón de logout (secundario)
    LOGOUT_BUTTON = """
        QPushButton {
            background: white;
            color: #6b7280;
            border: 2px solid #e5e7eb;
            border-radius: 10px;
            font-weight: 500;
            font-size: 14px;
            font-family: 'Segoe UI', Arial, sans-serif;
            padding: 12px 16px;
            min-height: 20px;
        }
        QPushButton:hover {
            color: #ef4444;
            border-color: #ef4444;
            background: #fef2f2;
        }
        QPushButton:pressed {
            background: #fee2e2;
        }
    """
    
    # Estilo del frame de estado de monitoreo
    STATUS_FRAME = """
        QFrame {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            border: 1px solid #e5e7eb;
        }
    """
    
    # Estilo del label de estado de monitoreo
    STATUS_LABEL = """
        QLabel {
            color: #374151;
            font-size: 12px;
            font-weight: 600;
            background: transparent;
            border: none;
            padding: 8px 12px;
        }
    """
    
    # Estilo de la barra de progreso para monitoreo
    PROGRESS_BAR = """
        QProgressBar {
            border: none;
            border-radius: 6px;
            background: #f3f4f6;
            text-align: center;
            height: 12px;
        }
        QProgressBar::chunk {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 #10b981, stop: 1 #059669);
            border-radius: 6px;
        }
    """
    
    @staticmethod
    def get_message_box_style(width, height, max_width):
        """Genera el estilo responsive para el MessageBox - SIN box-shadow"""
        return f"""
            QMessageBox {{
                background: white;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
                color: #374151;
                min-width: {width}px;
                max-width: {max_width}px;
                min-height: {height}px;
            }}
            QMessageBox QLabel {{
                color: #374151;
                font-size: 13px;
                padding: 15px;
                min-width: {width - 80}px;
                max-width: {max_width - 80}px;
            }}
            QMessageBox QPushButton {{
                background: #ef4444;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 13px;
                min-width: 100px;
                margin: 10px 5px;
            }}
            QMessageBox QPushButton:hover {{
                background: #dc2626;
            }}
            QMessageBox QPushButton:pressed {{
                background: #b91c1c;
            }}
        """

class MonitoringStatusIndicatorStyles:
    """Estilos para el indicador de estado de monitoreo"""
    
    COLORS = {
        "idle": "#6b7280",
        "monitoring": "#10b981", 
        "alert": "#ef4444",
        "warning": "#f59e0b",
        "error": "#ef4444"
    }
    
    @classmethod
    def get_status_style(cls, status):
        """Retorna el estilo para un estado específico"""
        color = cls.COLORS.get(status, cls.COLORS["idle"])
        return f"""
            QLabel {{
                border-radius: 8px;
                background-color: {color};
                min-width: 16px;
                min-height: 16px;
            }}
        """