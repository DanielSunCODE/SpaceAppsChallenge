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
SERIAL_PORT = os.getenv("ARD_PORT", "COM4")  # ⚠️ Cambiar COM6 si usas otro
BAUD = 9600
LOG_FILE = "sensor_log.txt"  # Archivo donde se guardan las lecturas

# ------------------------------------------------
# INICIALIZACIÓN DE LA API
# ------------------------------------------------
app = FastAPI(title="Arduino MQ135 Live Data")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Valor actual leído del Arduino
current_data = {"value": 0, "status": "Desconocido", "updated": False}


# ------------------------------------------------
# HILO QUE LEE EL PUERTO SERIAL DEL ARDUINO
# ------------------------------------------------
def serial_reader():
    global current_data
    print(f"Conectando al puerto {SERIAL_PORT}...")
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD, timeout=1)
        time.sleep(2)
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
            sensor_val = int(float(data.get("CO2", 0.0)))

            if sensor_val <= 720:
                status = "Bueno"
            elif sensor_val <= 1137:
                status = "Regular"
            else:
                status = "Malo"

            current_data = {
                "value": sensor_val,
                "status": status,
                "updated": True
            }

            log_line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} -> Valor: {sensor_val} | Estado: {status}\n"

            # Guardar en el archivo
            with open("sensor_log.txt", "a") as f:
                f.write(log_line)

            print(f"📡 {log_line.strip()}")

        except Exception as e:
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
        "value": 450,
        "status": "Regular",
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
