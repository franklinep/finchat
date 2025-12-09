import json
import random
import pathlib
from datetime import date, timedelta


SERIES = ["F001", "B001", "E001"]
RUCS = ["20123456789", "20654321987", "20456712345"]
MONTOS = [15.2, 48.5, 123.4, 350.0]


def generar_registro(idx: int) -> dict:
    return {
        "archivo": f"synthetic_{idx}.pdf",
        "campos_esperados": {
            "ruc_emisor": random.choice(RUCS),
            "serie": random.choice(SERIES),
            "numero": str(1000 + idx),
            "fecha_emision": (date.today() - timedelta(days=idx % 30)).isoformat(),
            "monto_total": f"{random.choice(MONTOS):.2f}",
            "items": [{"descripcion": "ITEM", "cantidad": 1, "precio_unitario": random.choice(MONTOS), "monto_item": random.choice(MONTOS)}],
        },
        "texto_completo": "RUC " + random.choice(RUCS) + " TOTAL " + f"{random.choice(MONTOS):.2f}",
    }


def main() -> None:
    base = pathlib.Path("app/data/sinteticos")
    base.mkdir(parents=True, exist_ok=True)
    labels = {}
    for i in range(20):
        reg = generar_registro(i)
        labels[reg["archivo"]] = reg
    with open(base / "labels.json", "w", encoding="utf-8") as f:
        json.dump(labels, f, ensure_ascii=False, indent=2)
    print(f"Generado labels.json con {len(labels)} entradas en {base}")


if __name__ == "__main__":
    main()
