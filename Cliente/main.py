# -*- coding: utf-8 -*-
import sys
import os
import logging
import subprocess
import faulthandler
import threading
import traceback

# ==========================================================================
# (1-B) FIX CRASH: OpenMP duplicado (libiomp5md.dll).
# El .spec de producción copia las DLLs de Intel MKL + libiomp5md.dll a la
# raíz del dist, y PyTorch trae su PROPIA copia de OpenMP. Con dos runtimes de
# OpenMP cargados, Intel ABORTA el proceso ("OMP: Error #15 ... already
# initialized"). Como el ejecutable es windowed (console=False), ese abort no
# muestra mensaje: la app se cierra en silencio al ejecutar la primera
# inferencia. Estas variables deben quedar FÍSICAMENTE ANTES de importar
# torch/cv2/ultralytics (los imports de App.* de abajo ya los arrastran).
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")


def _base_dir():
    """Directorio base compatible con PyInstaller (frozen) y desarrollo."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def resource_path(relative_path):
    """Ruta absoluta a un recurso empaquetado (UI/icon.ico, etc.).

    Resuelve tanto en desarrollo como dentro del bundle de PyInstaller:
    - frozen: sys._MEIPASS (carpeta temporal donde se extraen los datos).
    - desarrollo: directorio de este archivo (UI/ es hermano de main.py).
    """
    if hasattr(sys, '_MEIPASS'):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)


def resolve_data_path(relative_path):
    """Resolver un recurso de datos (p.ej. el modelo YOLO) de forma robusta.

    Usa la ruta relativa tal cual si existe respecto al cwd (comportamiento de
    desarrollo, sin cambios). Si no existe (típico en el ejecutable empaquetado,
    donde el cwd es el del .exe y los datos viven en el bundle), cae a
    resource_path(). Funciona igual en PyInstaller 5 (datos en la raíz) y 6
    (datos en _internal/). No cambia la arquitectura de inferencia.
    """
    if os.path.exists(relative_path):
        return relative_path
    bundled = resource_path(relative_path)
    return bundled if os.path.exists(bundled) else relative_path


# (1-A) Instrumentación para capturar CUALQUIER crash nativo futuro.
# faulthandler vuelca el stack de C/Python ante un abort/segfault (cosa que un
# try/except de Python NO puede interceptar) a crash_dump.log; sys/threading
# excepthook registran cualquier excepción de Python no capturada en el log.
# No cambia el comportamiento normal de la app.
_crash_dump_file = None


def _install_crash_handlers():
    global _crash_dump_file
    try:
        dump_path = os.path.join(_base_dir(), 'crash_dump.log')
        # Mantener el archivo abierto durante toda la vida del proceso: si se
        # cierra, faulthandler no podría escribir en el momento del crash.
        _crash_dump_file = open(dump_path, 'a', buffering=1, encoding='utf-8')
        faulthandler.enable(file=_crash_dump_file, all_threads=True)
    except Exception as e:
        # Si no se puede abrir el archivo, al menos a stderr.
        try:
            faulthandler.enable(all_threads=True)
        except Exception:
            pass
        print(f"No se pudo instalar faulthandler en archivo: {e}")

    def _log_uncaught(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        logging.exception(
            "Excepción no capturada (hilo principal): %s",
            exc_value,
            exc_info=(exc_type, exc_value, exc_tb),
        )

    sys.excepthook = _log_uncaught

    # threading.excepthook existe desde Python 3.8.
    if hasattr(threading, 'excepthook'):
        def _log_thread_uncaught(args):
            logging.error(
                "Excepción no capturada en hilo '%s':\n%s",
                getattr(args.thread, 'name', '?'),
                ''.join(traceback.format_exception(
                    args.exc_type, args.exc_value, args.exc_traceback)),
            )
        threading.excepthook = _log_thread_uncaught


# En Windows, evitar que los subprocesos (p.ej. nvidia-smi, que GPUtil invoca
# cada pocos segundos durante la deteccion) abran ventanas de consola que parpadean.
# Se envuelve subprocess.Popen para forzar CREATE_NO_WINDOW en toda la app.
if sys.platform.startswith('win'):
    _CREATE_NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
    _orig_popen_init = subprocess.Popen.__init__

    def _popen_no_window(self, *args, **kwargs):
        kwargs['creationflags'] = kwargs.get('creationflags', 0) | _CREATE_NO_WINDOW
        _orig_popen_init(self, *args, **kwargs)

    subprocess.Popen.__init__ = _popen_no_window

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, QSharedMemory
from PyQt5.QtGui import QIcon
from App.loginWindowClass import LoginWindow
from App.monitoringWindowClass import MonitoringWindow
from App.detectionWindowDual import DetectionWindowDual
from App.detection_tapo import DetectionTapo
from App.inference_engine import InferenceEngine
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
        
        # force=True es IMPRESCINDIBLE aqui. App.cameras_config emite logs al
        # importarse (load_settings_ini() corre a nivel de modulo), y esa primera
        # llamada a logging.info() instala un handler por defecto en el logger
        # raiz. A partir de ese momento basicConfig() NO HACE NADA si no se le
        # pasa force: el archivo app_log.log no llegaba a crearse nunca y la
        # aplicacion se quedaba sin rastro para diagnosticar. force=True descarta
        # los handlers previos y aplica de verdad esta configuracion.
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filemode='a',
            force=True,
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

def _log_configuracion_efectiva():
    """Registrar en el log la configuracion REALMENTE en uso al arrancar.

    App.cameras_config lee settings.ini al IMPORTARSE, es decir antes de que
    setup_logging() exista, asi que sus mensajes no llegan a app_log.log. Sin
    esto no habia forma de saber, mirando el log, si el ejecutable habia leido
    settings.ini o estaba corriendo con los valores por defecto del codigo.
    """
    try:
        from App.cameras_config import GLOBAL_CONFIG, _settings_ini_path
        ruta = _settings_ini_path()
        logging.info("settings.ini: %s (%s)",
                     ruta, "leido" if os.path.isfile(ruta) else "NO ENCONTRADO")
        for clave in ('model_path', 'confidence_threshold', 'analysis_interval',
                      'capture_interval', 'confirmation_frames',
                      'confirmation_window', 'min_box_area_ratio',
                      'max_box_area_ratio', 'inference_workers', 'server_url'):
            logging.info("  config efectiva | %-22s = %s", clave,
                         GLOBAL_CONFIG.get(clave))
    except Exception as exc:
        logging.warning("No se pudo registrar la configuracion efectiva: %s", exc)


class MainApplication(QObject):
    """Aplicación principal optimizada con soporte multi-cámara"""
    
    def __init__(self):
        super().__init__()
        setup_logging()
        _log_configuracion_efectiva()
        # Instalar handlers de crash DESPUÉS de configurar logging (para que el
        # excepthook pueda registrar) pero antes de crear ventanas/hilos.
        _install_crash_handlers()

        # Configurar aplicación Qt
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Weapon Detection System")
        self.app.setApplicationVersion("2.0 Multi-Camera")

        # Ícono a nivel de aplicación: lo heredan TODAS las ventanas (Login,
        # Monitoring, DetectionDual) y los QMessageBox por defecto. Antes solo
        # el ejecutable/barra de tareas tenían logo; las ventanas mostraban el
        # ícono genérico de Windows.
        try:
            icon_file = resource_path(os.path.join('UI', 'icon.ico'))
            if os.path.exists(icon_file):
                self.app.setWindowIcon(QIcon(icon_file))
            else:
                logging.warning(f"Ícono no encontrado en: {icon_file}")
        except Exception as e:
            logging.exception(f"No se pudo establecer el ícono de la aplicación: {e}")
        
        # Estado de la aplicación
        self.current_window = None
        self.detection_threads = {}  # Almacenar threads de detección activos
        self.engine = None  # Motor de inferencia COMPARTIDO (1 modelo para todas las cámaras)
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

            # Crear UN motor de inferencia COMPARTIDO (carga el modelo UNA sola vez
            # para todas las cámaras, en vez de una copia por cámara).
            model_path = resolve_data_path(GLOBAL_CONFIG['model_path'])
            self.engine = InferenceEngine(
                model_path,
                conf=GLOBAL_CONFIG.get('confidence_threshold', 0.5),
                iou=0.45,
                max_det=GLOBAL_CONFIG.get('max_detections', 10),
                num_workers=GLOBAL_CONFIG.get('inference_workers', 1),
                min_box_area_ratio=GLOBAL_CONFIG.get('min_box_area_ratio', 0.0),
                max_box_area_ratio=GLOBAL_CONFIG.get('max_box_area_ratio', 1.0),
            )
            try:
                self.engine.start()  # ÚNICA carga del modelo
            except Exception as e:
                logging.exception(f"Error al cargar el modelo de inferencia: {e}")
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(
                    None, "Error de Modelo",
                    f"No se pudo cargar el modelo de detección:\n\n{str(e)}\n\n"
                    f"Revise el archivo de log para más detalles."
                )
                self._teardown_engine()
                self.show_monitoring(self.current_token)
                return

            # Crear threads de detección para cada cámara habilitada
            self.detection_threads = {}

            for cam_num, config in cameras.items():
                logging.info("")
                logging.info(f"Configurando Cámara {cam_num}:")
                if str(config.get('brand', '')).lower() in ('webcam', 'local', 'usb'):
                    logging.info(f"  Fuente: Webcam local (índice {config.get('device_index', 0)})")
                else:
                    logging.info(f"  IP: {config.get('ip', '')}")
                    logging.info(f"  Usuario: {config.get('username', '')}")
                    logging.info(f"  Stream: {config.get('stream', '')}")
                logging.info(f"  Ubicación: {config.get('location', '')}")

                # Crear instancia de DetectionTapo (sin modelo propio: usa el engine compartido)
                detection = DetectionTapo(
                    model_path=GLOBAL_CONFIG['model_path'],
                    token=token,
                    location=config['location'],
                    receiver=receiver,
                    camera_config=config,
                    camera_id=cam_num,
                    engine=self.engine
                )

                self.detection_threads[cam_num] = detection
                logging.info(f"  Thread de detección creado para Cámara {cam_num}")
            
            # Crear ventana de visualización dual
            logging.info("")
            logging.info("Creando ventana de visualización dual...")
            self.current_window = DetectionWindowDual(self.detection_threads)
            # Al volver/detener desde la ventana de detección, regresar al menú
            # de configuración (en vez de cerrar la app o la sesión).
            self.current_window.closed.connect(self.on_detection_closed)
            self.current_window.show()
            
            logging.info("="*60)
            logging.info(f"✅ Sistema multi-cámara activo con {len(self.detection_threads)} cámara(s)")
            logging.info("="*60)
            
        except Exception as e:
            logging.exception(f"Error crítico al iniciar detección multi-cámara: {e}")
            # Limpiar cámaras ya creadas y el engine para NO dejar fugas
            # (modelo en RAM/VRAM + worker huérfano) si falla a mitad del arranque.
            for detection in self.detection_threads.values():
                try:
                    detection.stop()
                    detection.wait(3000)
                except Exception:
                    pass
            self.detection_threads.clear()
            self._teardown_engine()

            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                None, "Error Crítico",
                f"Error al iniciar sistema de detección:\n\n{str(e)}\n\n"
                f"Revise el archivo de log para más detalles."
            )
            # Volver a monitoring si hay error
            self.show_monitoring(self.current_token)

    def _teardown_engine(self):
        """Detener y liberar el motor de inferencia compartido de forma segura.

        Centraliza el apagado para que NINGÚN camino (cierre normal, logout o
        error a mitad del arranque) deje el engine vivo y huérfano (modelo en
        RAM/VRAM + worker daemon colgado).
        """
        if self.engine:
            try:
                self.engine.stop()
            except Exception as e:
                logging.error(f"Error al detener el motor de inferencia: {e}")
            self.engine = None

    def on_detection_closed(self):
        """Manejar cierre de ventana de detección"""
        logging.info("Detección cerrada - Deteniendo threads")
        
        # Detener todos los threads de detección PRIMERO
        for cam_num, detection in self.detection_threads.items():
            logging.info(f"Deteniendo thread de cámara {cam_num}")
            detection.stop()
            detection.wait(5000)  # Esperar máximo 5 segundos

        self.detection_threads.clear()

        # Detener el motor de inferencia DESPUÉS de las cámaras (apagado ordenado)
        self._teardown_engine()

        logging.info("Todos los threads detenidos - Volviendo a configuración")
        self.show_monitoring(self.current_token)

    def logout(self):
        """Cerrar sesión"""
        logging.info("Cerrando sesión de usuario")
        
        # Detener threads si están activos
        if self.detection_threads:
            for detection in self.detection_threads.values():
                detection.stop()
                detection.wait(5000)
            self.detection_threads.clear()

        # Detener el motor de inferencia compartido
        self._teardown_engine()

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