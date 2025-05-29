# styles.py - Archivo de estilos para la aplicación

class LoginWindowStyles:
    """Clase que contiene todos los estilos para la ventana de login"""
    
    # Estilo general de la ventana principal
    MAIN_WINDOW = """
        QMainWindow {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 #f8fafc, stop: 1 #e2e8f0);
            border: 2px solid #e5e7eb;
            border-radius: 12px;
        }
    """
    
    # Estilo del título
    TITLE_LABEL = """
        QLabel {
            color: #1f2937;
            font-size: 22px;
            font-weight: bold;
            font-family: 'Segoe UI', Arial, sans-serif;
            padding: 10px;
            background: rgba(255, 255, 255, 0.8);
            border-radius: 10px;
            border: 1px solid #e5e7eb;
        }
    """
    
    # Estilo para campos de entrada
    INPUT_FIELD = """
        QLineEdit {
            background: white;
            border: 2px solid #e5e7eb;
            border-radius: 10px;
            padding: 12px 16px;
            font-size: 14px;
            color: #374151;
            font-family: 'Segoe UI', Arial, sans-serif;
            min-height: 16px;
        }
        QLineEdit:focus {
            border-color: #3b82f6;
            outline: none;
        }
        QLineEdit:hover {
            border-color: #d1d5db;
        }
    """
    
    # Estilo para campo con error
    INPUT_FIELD_ERROR = """
        QLineEdit {
            background: white;
            border: 2px solid #fbbf24;
            border-radius: 10px;
            padding: 12px 16px;
            font-size: 14px;
            color: #374151;
            font-family: 'Segoe UI', Arial, sans-serif;
            min-height: 16px;
        }
        QLineEdit:focus {
            border-color: #f59e0b;
            outline: none;
        }
        QLineEdit:hover {
            border-color: #fbbf24;
        }
    """
    
    # Estilo del botón de login
    LOGIN_BUTTON = """
        QPushButton {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 #3b82f6, stop: 1 #1d4ed8);
            color: white;
            border: none;
            border-radius: 10px;
            font-weight: 600;
            font-size: 14px;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        QPushButton:hover {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 #2563eb, stop: 1 #1e40af);
        }
        QPushButton:pressed {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 #1d4ed8, stop: 1 #1e3a8a);
        }
        QPushButton:disabled {
            background: #9ca3af;
            color: #f3f4f6;
        }
    """
    
    # Estilo del botón de registro
    REGISTER_BUTTON = """
        QPushButton {
            background: white;
            color: #6b7280;
            border: 2px solid #e5e7eb;
            border-radius: 10px;
            font-weight: 500;
            font-size: 14px;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        QPushButton:hover {
            color: #374151;
            border-color: #3b82f6;
            background: #f8fafc;
        }
        QPushButton:pressed {
            background: #f1f5f9;
        }
    """
    
    # Estilo de las etiquetas
    LABEL_STYLE = """
        QLabel {
            color: #374151;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-weight: 600;
            font-size: 13px;
            background: transparent;
            border: none;
        }
    """
    
    # Estilo del frame de estado
    STATUS_FRAME = """
        QFrame {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 17px;
            border: 1px solid #e5e7eb;
        }
    """
    
    # Estilo del label de estado
    STATUS_LABEL = """
        QLabel {
            color: #374151;
            font-size: 11px;
            font-weight: 500;
            background: transparent;
            border: none;
        }
    """
    
    # Estilo de la barra de progreso
    PROGRESS_BAR = """
        QProgressBar {
            border: none;
            border-radius: 4px;
            background: #f3f4f6;
            text-align: center;
        }
        QProgressBar::chunk {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 #3b82f6, stop: 1 #06b6d4);
            border-radius: 4px;
        }
    """
    
    # Estilo de la barra de progreso en éxito
    PROGRESS_BAR_SUCCESS = """
        QProgressBar {
            border: none;
            border-radius: 4px;
            background: #f3f4f6;
            text-align: center;
        }
        QProgressBar::chunk {
            background: #10b981;
            border-radius: 4px;
        }
    """
    
    @staticmethod
    def get_message_box_style(width, height, max_width):
        """Genera el estilo responsive para el MessageBox"""
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

class StatusIndicatorStyles:
    """Estilos para el indicador de estado"""
    
    COLORS = {
        "checking": "#f59e0b",
        "connected": "#10b981", 
        "disconnected": "#ef4444",
        "error": "#ef4444",
        "default": "#6b7280"
    }
    
    @classmethod
    def get_status_style(cls, status):
        """Retorna el estilo para un estado específico"""
        color = cls.COLORS.get(status, cls.COLORS["default"])
        return f"""
            QLabel {{
                border-radius: 6px;
                background-color: {color};
            }}
        """