import cv2
import os

# ========================================
# CAMBIA ESTOS VALORES
# ========================================
IP_CAMARA = "192.168.1.10"  # IP que viste en la app Tapo
USUARIO = "Lander"             # Usuario que creaste en Camera Account
PASSWORD = "lander123"         # Contraseña que creaste

# ========================================
# NO CAMBIES NADA DE AQUÍ PARA ABAJO
# ========================================

print("="*60)
print("🔧 TEST DE CONEXIÓN TAPO C310")
print("="*60)
print(f"IP: {IP_CAMARA}")
print(f"Usuario: {USUARIO}")
print(f"Contraseña: {'*' * len(PASSWORD)}")
print("="*60)

# Construir URL RTSP
rtsp_url = f"rtsp://{USUARIO}:{PASSWORD}@{IP_CAMARA}:554/stream1"

# Configuración para baja latencia
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
    "rtsp_transport;udp|"
    "fflags;nobuffer|"
    "flags;low_delay"
)

print("\n🔌 Intentando conectar con UDP...")
cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

if not cap.isOpened():
    print("❌ UDP falló, intentando con TCP...")
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

if not cap.isOpened():
    print("\n❌ ERROR: No se pudo conectar")
    print("\n🔍 VERIFICAR:")
    print("1. ¿Creaste Camera Account en app Tapo?")
    print("2. ¿Las credenciales son correctas?")
    print("3. ¿La IP es correcta?")
    print("4. ¿La cámara está encendida y en la misma red?")
    exit()

print("✅ ¡CONEXIÓN EXITOSA!")

# Obtener info del stream
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print(f"📐 Resolución: {width}x{height}")

print("\n📹 Mostrando video (Presiona 'q' para salir)...")

frame_count = 0
import time
start_time = time.time()

while True:
    ret, frame = cap.read()
    
    if not ret:
        print("⚠️ Error al leer frame")
        break
    
    frame_count += 1
    elapsed = time.time() - start_time
    fps = frame_count / elapsed if elapsed > 0 else 0
    
    # Mostrar info en pantalla
    cv2.putText(frame, f"Frames: {frame_count}", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(frame, f"FPS: {fps:.1f}", (10, 60), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(frame, "TAPO C310 OK", (10, 90), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    cv2.imshow('Tapo C310 Test', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

print(f"\n✅ Prueba completada!")
print(f"Frames capturados: {frame_count}")
print(f"Tiempo: {elapsed:.1f}s")
print(f"FPS promedio: {fps:.1f}")
