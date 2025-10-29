# -*- coding: utf-8 -*-
import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, QSharedMemory
from App.loginWindowClass import LoginWindow
from App.monitoringWindowClass import MonitoringWindow
from App.detectionWindow import DetectionWindow
from App.detectionWindowDual import DetectionWindowDual
from App.detection_tapo import DetectionTapo
from App.cameras_config import GLOBAL_CONFIG

# Configurar codificación UTF-8 para la aplicación
if sys.platform.startswith('win'):
    try:
        import locale
        locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
    except:
        pass  # Si no está disponible, continuar sin configurar

def setup_logging():
    """Configurar sistema de logging"""
    try:
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))
        
        log_file = os.path.join(application_path, 'app_log.log')
        
        # Configurar logging sin el parámetro encoding para compatibilidad
        logging.basicConfig(
            filename=log_file, 
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filemode='a'
        )
        
        # También logging a consola para desarrollo
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logging.getLogger().addHandler(console_handler)
        
        # Configurar codificación manualmente para el archivo de log
        log_handler = None
        for handler in logging.getLogger().handlers:
            if hasattr(handler, 'stream') and hasattr(handler.stream, 'name'):
                if handler.stream.name == log_file:
                    log_handler = handler
                    break
        
        # Si se encontró el handler del archivo, intentar configurar encoding
        if log_handler and hasattr(log_handler, 'stream'):
            try:
                # Para Python < 3.9, configurar encoding a nivel de sistema
                import codecs
                if hasattr(log_handler.stream, 'reconfigure'):
                    log_handler.stream.reconfigure(encoding='utf-8')
            except:
                pass  # Si falla, continuar sin configurar encoding
        
        logging.info(f"Logging optimizado iniciado. Archivo: {log_file}")
        
    except Exception as e:
        print(f"Error al configurar logging: {e}")
        # Configuración de fallback sin encoding
        logging.basicConfig(
            level=logging.INFO, 
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )
        logging.error(f"No se pudo configurar archivo de log. Usando consola. Error: {e}")

class MainApplication(QObject):
    """Aplicación principal optimizada con soporte multi-cámara"""
    
    def __init__(self):
        super().__init__()
        setup_logging()
        
        # Configurar aplicación Qt
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Weapon Detection System")
        self.app.setApplicationVersion("2.0 Multi-Camera")
        
        # Estado de la aplicación
        self.current_window = None
        self.detection_threads = {}  # Almacenar threads de detección activos
        self.is_logged_in = False
        self.current_token = None
        
        logging.info("Aplicación principal multi-cámara inicializada")

    def start(self):
        """Iniciar aplicación"""
        logging.info("=== Iniciando Weapon Detection System v2.0 Multi-Cámara ===")
        self.show_login()
        return self.app.exec_()

    def show_login(self):
        """Mostrar ventana de login"""
        if not self.is_logged_in:
            logging.info("Mostrando ventana de login")
            self.close_current_window()
            self.current_window = LoginWindow()
            self.current_window.loginSuccessful.connect(self.on_login_successful)
            self.current_window.show()
        else:
            logging.debug("Usuario ya autenticado, saltando login")

    def on_login_successful(self, token):
        """Manejar login exitoso"""
        logging.info("Login exitoso - Iniciando sesión")
        self.is_logged_in = True
        self.current_token = token
        self.show_monitoring(token)

    def show_monitoring(self, token):
        """Mostrar ventana de configuración de monitoreo"""
        logging.info("Mostrando ventana de configuración de monitoreo multi-cámara")
        self.close_current_window()
        self.current_window = MonitoringWindow(token)
        self.current_window.startMonitoringSignal.connect(self.show_detection)
        self.current_window.show()

    def show_detection(self, cameras_config):
        """
        Mostrar ventana de detección multi-cámara
        
        Args:
            cameras_config: Dict con configuración
                {
                    'token': str,
                    'receiver': str,
                    'cameras': {
                        cam_num: {config_dict},
                        ...
                    }
                }
        """
        try:
            logging.info("="*60)
            logging.info("Iniciando sistema de detección multi-cámara")
            logging.info("="*60)
            
            # Extraer datos de configuración
            token = cameras_config.get('token')
            receiver = cameras_config.get('receiver')
            cameras = cameras_config.get('cameras', {})
            
            if not cameras:
                logging.error("No hay cámaras configuradas")
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(
                    None, "Error",
                    "No hay cámaras configuradas para iniciar."
                )
                return
            
            logging.info(f"Token: {token[:10]}...")
            logging.info(f"Receptor: {receiver}")
            logging.info(f"Número de cámaras: {len(cameras)}")
            
            # Cerrar ventana de configuración
            self.close_current_window()
            
            # Crear threads de detección para cada cámara habilitada
            self.detection_threads = {}
            
            for cam_num, config in cameras.items():
                logging.info(f"")
                logging.info(f"Configurando Cámara {cam_num}:")
                logging.info(f"  IP: {config['ip']}")
                logging.info(f"  Usuario: {config['username']}")
                logging.info(f"  Stream: {config['stream']}")
                logging.info(f"  Ubicación: {config['location']}")
                
                # Crear instancia de DetectionTapo
                detection = DetectionTapo(
                    model_path=GLOBAL_CONFIG['model_path'],
                    token=token,
                    location=config['location'],
                    receiver=receiver,
                    camera_config=config,
                    camera_id=cam_num
                )
                
                self.detection_threads[cam_num] = detection
                logging.info(f"  Thread de detección creado para Cámara {cam_num}")
            
            # Crear ventana de visualización dual
            logging.info(f"")
            logging.info("Creando ventana de visualización dual...")
            self.current_window = DetectionWindowDual(self.detection_threads)
            self.current_window.show()
            
            logging.info("="*60)
            logging.info(f"✅ Sistema multi-cámara activo con {len(self.detection_threads)} cámara(s)")
            logging.info("="*60)
            
        except Exception as e:
            logging.exception(f"Error crítico al iniciar detección multi-cámara: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                None, "Error Crítico",
                f"Error al iniciar sistema de detección:\n\n{str(e)}\n\n"
                f"Revise el archivo de log para más detalles."
            )
            # Volver a monitoring si hay error
            self.show_monitoring(self.current_token)

    def on_detection_closed(self):
        """Manejar cierre de ventana de detección"""
        logging.info("Detección cerrada - Deteniendo threads")
        
        # Detener todos los threads de detección
        for cam_num, detection in self.detection_threads.items():
            logging.info(f"Deteniendo thread de cámara {cam_num}")
            detection.stop()
            detection.wait(5000)  # Esperar máximo 5 segundos
        
        self.detection_threads.clear()
        logging.info("Todos los threads detenidos - Volviendo a configuración")
        self.show_monitoring(self.current_token)

    def logout(self):
        """Cerrar sesión"""
        logging.info("Cerrando sesión de usuario")
        
        # Detener threads si están activos
        if self.detection_threads:
            for detection in self.detection_threads.values():
                detection.stop()
            self.detection_threads.clear()
        
        self.is_logged_in = False
        self.current_token = None
        self.close_current_window()
        self.show_login()

    def close_current_window(self):
        """Cerrar ventana actual de forma segura"""
        if self.current_window:
            window_type = type(self.current_window).__name__
            logging.debug(f"Cerrando ventana: {window_type}")
            
            # Cerrar ventana de forma segura
            try:
                self.current_window.close()
                self.current_window.deleteLater()
            except:
                pass
            
            self.current_window = None

def main():
    """Función principal"""
    # Verificar que no haya otra instancia ejecutándose
    shared_memory = QSharedMemory("WeaponDetectionApp_v2")
    if shared_memory.attach():
        print("La aplicación ya está ejecutándose")
        logging.warning("Intento de ejecutar segunda instancia - Cancelando")
        sys.exit(1)
    
    if not shared_memory.create(1):
        print("No se pudo crear memoria compartida")
        logging.error("Error al crear memoria compartida")
        sys.exit(1)
    
    try:
        # Crear y ejecutar aplicación
        main_app = MainApplication()
        exit_code = main_app.start()
        
        logging.info(f"Aplicación terminada con código: {exit_code}")
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        logging.info("Aplicación interrumpida por usuario (Ctrl+C)")
        sys.exit(0)
        
    except Exception as e:
        logging.exception(f"Error crítico en aplicación: {e}")
        sys.exit(1)
        
    finally:
        # Limpiar memoria compartida
        shared_memory.detach()
        logging.info("Recursos liberados correctamente")

if __name__ == '__main__':
    main()