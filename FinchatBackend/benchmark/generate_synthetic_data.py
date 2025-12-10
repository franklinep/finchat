import json
import random
import pathlib
from datetime import date, timedelta

# Constants
RUCS = ["20556519065", "10199483761"]
SERIES = ["B001", "F001", "E001"]
ITEMS_POOL = [
    {"desc": "WANTAN FRITO", "price": 15.00},
    {"desc": "CHAUFA YEN YEN", "price": 24.00},
    {"desc": "CHAUFA ESPECIAL", "price": 20.50},
    {"desc": "MENU FUN KING C", "price": 21.00},
    {"desc": "GASEOSA 1.5 LIT", "price": 12.50},
    {"desc": "TAPER", "price": 1.50},
    {"desc": "POLLO A LA BRASA", "price": 55.00},
    {"desc": "PAPAS FRITAS", "price": 12.00},
    {"desc": "ENSALADA", "price": 8.00},
    {"desc": "INKA KOLA 1L", "price": 9.00},
]

def generate_receipt_text(data: dict) -> str:
    """
    Generates a synthetic OCR text representation of the receipt.
    """
    lines = []
    lines.append("CHIFA YEN YEN")
    lines.append("TEAM SABOR SAC")
    lines.append(f"RUC:{data['ruc_emisor']}")
    lines.append("AV.ANTUNEZ DE MAYOLO Nro. 1230")
    lines.append("LIMA - LIMA - LOS OLIVOS")
    lines.append("LOCAL:0001")
    lines.append("BOLETA DE VENTA ELECTRONICA")
    lines.append(f"{data['serie']} No. {data['numero']} Mesa 29Sala 2")
    lines.append(f"CAJERO: BALVIN {data['fecha_emision_fmt']}     16:00:39")
    lines.append("CLIENTE:ABELESTEBAN ESPINOZA PARI")
    lines.append("DNI:75524035")
    lines.append("Descripcion   Cant.  P.U.   Dscto  P.Total")
    lines.append("====================================")

    for item in data['items']:
        # Format: DESC  QTY  UNIT_PRICE  DISC  TOTAL
        # Truncate desc to fit or just let it be loose like OCR
        line = f"{item['descripcion']:<14} {item['cantidad']}  {item['precio_unitario']}  0    {item['monto_item']}"
        lines.append(line)

    lines.append("====================================")
    lines.append(f"SUB TOTAL    S /.{data['monto_total']}")
    # Simplified tax calc for display
    op_gravada = float(data['monto_total']) / 1.18
    igv = float(data['monto_total']) - op_gravada
    lines.append(f"OP.GRAVADA S/.{op_gravada:.2f}")
    lines.append(f"IGV 18%   S/.{igv:.2f}")
    lines.append(f"TOTAL A PAGAR   S/.{data['monto_total']}")
    lines.append(f"VISA {data['monto_total']}  0.00")
    lines.append("SON:")
    lines.append("(CIENT")
    lines.append("(CERO SOLES CON 00/100 SOLES)")
    lines.append("14Bu02LUHUcPfmReVQpDOdyP6n8=")
    lines.append("Autorizado_mediante resolución")
    lines.append("Nro.0340050004044 /SUNAT")
    lines.append("de Venta Electronica.")
    lines.append("www.chifayenyen.com")
    lines.append("facebook.com/yenyenoficial")
    lines.append("Para consultar el documento Ingrese a")
    lines.append("www.docele.pe/intercamt io/consulta")
    lines.append("CLIENTE:")
    lines.append("ABECESTÉBaN eSPiNOZA FArI")
    lines.append("Oíreccion de entrega:")
    lines.append("GRACIAS POR SU VISITA")

    return "\n".join(lines)

def generate_synthetic_data(num_samples: int = 10):
    data_list = []

    for i in range(num_samples):
        ruc = random.choice(RUCS)
        serie = random.choice(SERIES)
        numero = f"{random.randint(100000, 999999)}"
        # Random date in 2025
        fecha = date(2025, random.randint(1, 12), random.randint(1, 28))
        fecha_fmt = fecha.strftime("%d/%m/%Y")
        fecha_iso = fecha.isoformat()

        # Generate items
        num_items = random.randint(1, 5)
        selected_items = random.sample(ITEMS_POOL, num_items)

        items_data = []
        total = 0.0

        for item in selected_items:
            qty = random.randint(1, 3)
            monto = qty * item['price']
            total += monto
            items_data.append({
                "descripcion": item['desc'],
                "cantidad": str(qty),
                "precio_unitario": f"{item['price']:.2f}",
                "monto_item": f"{monto:.2f}"
            })

        total_str = f"{total:.2f}"

        # Determine type based on serie
        tipo_comp = "factura" if serie.startswith("F") else "boleta"

        campos_esperados = {
            "comprobante": {
                "tipo_comprobante": tipo_comp,
                "serie": serie,
                "numero": str(int(numero)), # Remove leading zeros for consistency with prompt rules
                "fecha_emision": fecha_iso,
                "moneda": "PEN",
                "monto_total": float(total_str),
                "origen": "electronico"
            },
            "emisor": {
                "ruc": ruc,
                "razon_social": "CHIFA YEN YEN", # Hardcoded in text gen
                "nombre_comercial": None
            },
            "items": [
                {
                    "descripcion": item["descripcion"],
                    "cantidad": float(item["cantidad"]),
                    "precio_unitario": float(item["precio_unitario"]),
                    "monto_item": float(item["monto_item"])
                }
                for item in items_data
            ],
            "cliente": {
                "nombre_cliente": "ABELESTEBAN ESPINOZA PARI", # Hardcoded in text gen
                "doc_cliente": "75524035",
                "tipo_doc_cliente": "DNI"
            }
        }

        # Helper dict for text generation
        gen_data = {
            "ruc_emisor": ruc,
            "serie": serie,
            "numero": numero,
            "fecha_emision_fmt": fecha_fmt,
            "monto_total": total_str,
            "items": items_data
        }

        texto_ocr = generate_receipt_text(gen_data)

        data_list.append({
            "texto_ocr": texto_ocr,
            "campos_esperados": campos_esperados
        })

    return data_list

def main():
    output_path = pathlib.Path("benchmark/data/synthetic_ocr.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = generate_synthetic_data(20) # Generate 20 samples

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(data)} synthetic records to {output_path}")

if __name__ == "__main__":
    main()
