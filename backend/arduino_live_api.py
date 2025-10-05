# ================================================================
# API en tiempo real para datos del sensor MQ135
# Proyecto: NASA Space Apps Challenge - Saltillo
# Autor: Ángel Alejandro Morales Aguilar
# ================================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import serial, json, threading, os, time

# ------------------------------------------------
# CONFIGURACIÓN DEL PUERTO SERIAL
# ------------------------------------------------
# ⚠️ En Windows usa COMx (ej: "COM6")
# ⚠️ En macOS/Linux usa /dev/tty.usbmodemXXXX o /dev/ttyACM0
SERIAL_PORT = os.getenv("ARD_PORT", "COM6")
BAUD = 9600

# ------------------------------------------------
# INICIALIZACIÓN DE LA API
# ------------------------------------------------
app = FastAPI(title="Arduino MQ135 Live Data")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite conexión desde el frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Valor actual leído del Arduino
current_data = {"quality": 0, "status": "Desconocido", "updated": False}


# ------------------------------------------------
# FUNCIÓN PARA CONVERTIR LECTURA A ESCALA 0–100
# ------------------------------------------------
def sensor_to_quality(co2_ppm: float) -> float:
    """
    Convierte CO2 (ppm) en un índice 0–100 aproximado.
    Cuanto menor sea el CO2, mejor la calidad del aire.
    """
    q = (2000.0 - co2_ppm) / (2000.0 - 350.0) * 100.0
    return max(0.0, min(100.0, q))


# ------------------------------------------------
# HILO QUE LEE EL PUERTO SERIAL DEL ARDUINO
# ------------------------------------------------
def serial_reader():
    global current_data
    print(f"Conectando al puerto {SERIAL_PORT}...")
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD, timeout=1)
        time.sleep(2)  # Esperar a que el Arduino se estabilice
        print("✅ Conectado correctamente al Arduino.")
    except Exception as e:
        print(f"❌ No se pudo conectar al Arduino ({e})")
        ser = None

    while True:
        if ser is None:
            time.sleep(2)
            continue

        try:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if not line or not line.startswith("{"):
                continue

            data = json.loads(line)
            co2 = float(data.get("CO2", 0.0))
            q = round(sensor_to_quality(co2), 1)
            status = "Bueno" if q >= 65 else ("Regular" if q >= 40 else "Malo")

            current_data = {
                "quality": q,
                "status": status,
                "updated": True
            }

            print(f"📡 {time.strftime('%H:%M:%S')} -> Calidad: {q} ({status})")

        except Exception as e:
            # Si el puerto lanza error o el JSON llega incompleto, se ignora
            # print(f"Error lectura: {e}")
            continue


# Lanzar el hilo de lectura en segundo plano
threading.Thread(target=serial_reader, daemon=True).start()


# ------------------------------------------------
# ENDPOINT PARA OBTENER EL DATO ACTUAL
# ------------------------------------------------
@app.get("/live")
def get_live_data():
    """
    Devuelve la última lectura del sensor MQ135.
    Ejemplo:
    {
        "quality": 72.5,
        "status": "Bueno",
        "updated": true
    }
    """
    return current_data


# ------------------------------------------------
# ENDPOINT DE PRUEBA
# ------------------------------------------------
@app.get("/")
def root():
    return {
        "message": "API en tiempo real del sensor MQ135 activa",
        "endpoint": "/live",
        "author": "Ángel Alejandro Morales Aguilar"
    }