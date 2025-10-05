# backend/load_data.py
import os
import json
import pandas as pd
from datetime import timezone

# === Rutas (tu estructura actual) ===
CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "saltillo_gases_week_2025-10-04_15min_with_date.csv")
OUT_BACKEND_JSON = os.path.join(os.path.dirname(__file__), "air_quality_data.json")
OUT_PUBLIC_DIR = os.path.join(os.path.dirname(__file__), "..", "public", "data")
OUT_PUBLIC_JSON = os.path.join(OUT_PUBLIC_DIR, "air_quality_data.json")

# === Límites simples (unidades aproximadas para tu dataset) ===
LIMITS = {
    "no2_value": 100.0,     # ppb
    "o3_value": 70.0,       # ppb (si viene negativo, usamos abs)
    "hcho_value": 0.002,    # ~ 2e-3 (tu CSV maneja ~1e-4 a 1e-3)
    "so2_value": 0.02,      # 2e-2
    "co_value": 9.0,        # 9 ppm
}

COLOR_BY_QUALITY = {
    "Excelente": "#00c853",  # verde intenso
    "Buena":     "#4caf50",  # verde
    "Moderada":  "#ffb300",  # ámbar
    "Mala":      "#ff7043",  # naranja
    "Muy Mala":  "#e53935",  # rojo
}

def quality_from_pct(pct):
    """pct es el % de 'calidad' (100 = excelente, 0 = muy mala)."""
    if pct >= 90:   return "Excelente"
    if pct >= 75:   return "Buena"
    if pct >= 60:   return "Moderada"
    if pct >= 40:   return "Mala"
    return "Muy Mala"

def color_from_quality(q):
    return COLOR_BY_QUALITY.get(q, "#9e9e9e")

def clamp01(x):  # limita a [0,1]
    return max(0.0, min(1.0, x))

def read_csv():
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"No existe el CSV en: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)
    # columnas esperadas (según tu captura): datetime, date_only, zone, latitude, longitude, no2_value, o3_value, hcho_value, so2_value, co_value
    # normalización de fecha
    dt = pd.to_datetime(df["datetime"], errors="coerce", utc=True)
    if dt.dt.tz is not None:
        df["datetime"] = dt.dt.tz_convert(timezone.utc).dt.tz_localize(None)
    else:
        df["datetime"] = dt
    return df

def compute_row_quality(row):
    # porcentaje “de uso del límite” (1.0 = alcanzó el límite)
    use_no2 = abs(row.get("no2_value", 0.0)) / LIMITS["no2_value"]
    use_o3  = abs(row.get("o3_value",  0.0)) / LIMITS["o3_value"]
    use_hcho= abs(row.get("hcho_value",0.0)) / LIMITS["hcho_value"]
    use_so2 = abs(row.get("so2_value", 0.0)) / LIMITS["so2_value"]
    use_co  = abs(row.get("co_value",  0.0)) / LIMITS["co_value"]

    # peor gas domina (conservador)
    worst_use = max(use_no2, use_o3, use_hcho, use_so2, use_co)
    worst_use = clamp01(worst_use)

    aqi_pct = round((1.0 - worst_use) * 100.0, 1)  # 0–100
    quality = quality_from_pct(aqi_pct)
    color = color_from_quality(quality)

    # porcentajes individuales por claridad en el popup
    gas_pct = {
        "no2_pct": round((1.0 - clamp01(use_no2)) * 100.0, 1),
        "o3_pct":  round((1.0 - clamp01(use_o3 )) * 100.0, 1),
        "hcho_pct":round((1.0 - clamp01(use_hcho)) * 100.0, 1),
        "so2_pct": round((1.0 - clamp01(use_so2)) * 100.0, 1),
        "co_pct":  round((1.0 - clamp01(use_co )) * 100.0, 1),
    }
    return aqi_pct, quality, color, gas_pct

def main():
    print("📖 Leyendo CSV…")
    df = read_csv()

    # —— ESTRATEGIA DE SALIDA ——
    # Tomamos la medición más reciente por zona (puedes cambiar a promedio por ‘date_only’ o por ‘zona’ si quieres).
    df = df.sort_values("datetime")
    last_by_zone = df.groupby("zone", as_index=False).tail(1)

    records = []
    for _, row in last_by_zone.iterrows():
        aqi_pct, quality, color, gas_pct = compute_row_quality(row)
        rec = {
            "datetime": row["datetime"].isoformat() if pd.notna(row["datetime"]) else None,
            "zone": row.get("zone"),
            "latitude": float(row.get("latitude", 0.0)),
            "longitude": float(row.get("longitude", 0.0)),

            # valores crudos
            "no2_value": float(row.get("no2_value", 0.0)),
            "o3_value":  float(row.get("o3_value", 0.0)),
            "hcho_value":float(row.get("hcho_value", 0.0)),
            "so2_value": float(row.get("so2_value", 0.0)),
            "co_value":  float(row.get("co_value", 0.0)),

            # “porcentaje de calidad” por gas (100 = limpio respecto a su límite)
            **gas_pct,

            # global / semáforo
            "AQI_Global": aqi_pct,
            "Calidad_Aire": quality,
            "color": color,
        }
        records.append(rec)

    # Asegurar carpeta public/data
    os.makedirs(OUT_PUBLIC_DIR, exist_ok=True)

    # Escribir JSON (backend y public)
    with open(OUT_BACKEND_JSON, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    with open(OUT_PUBLIC_JSON, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"✅ Generado JSON con {len(records)} zonas.")
    print(f"  • {OUT_BACKEND_JSON}")
    print(f"  • {OUT_PUBLIC_JSON}")

if __name__ == "__main__":
    main()

