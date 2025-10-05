import pandas as pd
import json
import os

# 📁 Ruta del archivo CSV
DATA_PATH = os.path.join(os.path.dirname(__file__), "../data/saltillo_gases_week_2025-10-04_15min_with_date.csv")

# 📊 Límites máximos (en µg/m³ o equivalentes normalizados)
LIMITS = {
    "no2_value": 200,
    "o3_value": 180,
    "hcho_value": 0.1,
    "so2_value": 125,
    "co_value": 10
}

# 🎨 Colores según calidad del aire
COLOR_SCALE = [
    ("Buena", "#00e400"),
    ("Moderada", "#ffff00"),
    ("Mala", "#ff7e00"),
    ("Muy Mala", "#ff0000")
]

def calculate_percentage(value, limit):
    pct = (value / limit) * 100
    return min(pct, 100)

def classify_quality(avg_pct):
    if avg_pct <= 50:
        return "Buena", COLOR_SCALE[0][1]
    elif avg_pct <= 75:
        return "Moderada", COLOR_SCALE[1][1]
    elif avg_pct <= 90:
        return "Mala", COLOR_SCALE[2][1]
    else:
        return "Muy Mala", COLOR_SCALE[3][1]

def main():
    print("📖 Leyendo datos...")
    df = pd.read_csv(DATA_PATH)

    zones = []
    print("🧮 Calculando promedios por zona...")
    for zone, group in df.groupby("zone"):
        row = {"zone": zone}
        avg_pcts = []

        for gas, limit in LIMITS.items():
            avg_val = group[gas].mean()
            pct = calculate_percentage(avg_val, limit)
            avg_pcts.append(pct)
            row[gas] = round(avg_val, 4)
            row[f"{gas}_pct"] = round(pct, 2)

        avg_aqi = sum(avg_pcts) / len(avg_pcts)
        quality, color = classify_quality(avg_aqi)
        row["AQI_Global"] = round(avg_aqi, 2)
        row["Calidad_Aire"] = quality
        row["Color"] = color
        zones.append(row)

    # 📤 Guardar como JSON
    output_path = os.path.join(os.path.dirname(__file__), "air_quality_data.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(zones, f, ensure_ascii=False, indent=2)

    print(f"✅ Archivo guardado en: {output_path}")

if __name__ == "__main__":
    main()


