import json
import os
import random
from datetime import datetime, timedelta, timezone

TZ = timezone(timedelta(hours=-5))  # hora de Colombia
DISPOSITIVOS = [1, 2]
LECTURAS = 144  # 12 h, una lectura cada 5 min

random.seed(int(os.environ.get("SEED", "42")))
inicio = datetime(2026, 10, 5, 6, 0, tzinfo=TZ)

ruta = os.path.join("data", "lecturas.jsonl")
os.makedirs("data", exist_ok=True)

with open(ruta, "w", encoding="utf-8") as f:
    for device_id in DISPOSITIVOS:
        for i in range(LECTURAS):
            msg = {
                "device_id": device_id,
                "ts": (inicio + timedelta(minutes=5 * i)).isoformat(),
                "p_ac": round(random.uniform(0, 5.0), 3),          # kW
                "irradiancia": round(random.uniform(0, 1000), 1),  # W/m2
                "temp_modulo": round(random.uniform(18, 60), 1),   # grados C
                "voltaje_dc": round(random.uniform(300, 600), 1),  # V (campo nuevo)
            }
            if random.random() < 0.03:
                msg["alarma"] = "GRID_FAULT"
            f.write(json.dumps(msg) + "\n")

print(f"Archivo generado: {ruta} ({len(DISPOSITIVOS) * LECTURAS} lecturas)")
