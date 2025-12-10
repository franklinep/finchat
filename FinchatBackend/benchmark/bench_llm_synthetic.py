import argparse
import argparse
import json
import time
import statistics
import pathlib
import requests
from typing import List, Dict, Any

# from app.config.settings import settings
OLLAMA_HOST = "http://localhost:11434"

# PROMPT FROM app/features/agents/prompts/parseador.py
PROMPT_SISTEMA = """
Eres un experto en extracción de datos de comprobantes de pago peruanos.
Tu tarea es recibir texto crudo proveniente de un OCR y extraer los campos estructurados en formato JSON estricto.

### CAMPOS A EXTRAER:
1. COMPROBANTE: tipo (factura/boleta), serie, número, fecha (YYYY-MM-DD), moneda, monto total, origen.
2. EMISOR: RUC (11 dígitos), razón social.
3. ITEMS: lista de ítems con descripción, cantidad, precio unitario, monto.
4. CLIENTE: nombre, documento y tipo de documento (si aparecen).

### REGLAS IMPORTANTES:
- RUC: Debe tener 11 dígitos. Corrige errores comunes de OCR (C->O, O->0, I->1, B->8, S->5, Z->2).
- Serie: Generalmente letra + 3 dígitos (ej: F001, B001, EB01).
- Número: Elimina ceros a la izquierda innecesarios.
- Fecha: Formato obligatorio YYYY-MM-DD.
- Moneda: Si no se especifica, asume "PEN".
- Origen: 'electronico' si parece un PDF generado digitalmente, 'fisico' si parece escaneo.
- Items: Extrae TODOS los ítems. No inventes descripciones.

### EJEMPLOS DE REFERENCIA (FEW-SHOT):

--- EJEMPLO 1 ---
Input OCR:
"TELLO MENDOZA HUMBELINA
RUC: 10470799531
BOLETA DE VENTA ELECTRONICA
Serie: EB01 - Número: 4847
Fecha: 02/08/2025
...
CONSUMO     1.00    60.00     66.00
Total: S/ 66.00"

Output JSON:
{
  "comprobante": {
    "tipo_comprobante": "boleta", "serie": "EB01", "numero": "4847",
    "fecha_emision": "2025-08-02", "moneda": "PEN", "monto_total": 66.00, "origen": "electronico"
  },
  "emisor": { "ruc": "10470799531", "razon_social": "TELLO MENDOZA HUMBELINA", "nombre_comercial": null },
  "items": [{ "descripcion": "CONSUMO", "cantidad": 1.0, "precio_unitario": 60.00, "monto_item": 66.00 }],
  "cliente": { "nombre_cliente": null, "doc_cliente": null, "tipo_doc_cliente": null }
}

--- EJEMPLO 2 ---
Input OCR:
"FACTURA ELECTRONICA
COMERCIAL OMEGA SAC RUC: 20345678901
F001-000123 Fecha: 15/07/2025
Cliente: JUAN PEREZ LOPEZ DNI: 75524035
...
Servicio Contable     1      500.00    500.00
Asesoría Tributaria   2      200.00    400.00
TOTAL: S/ 900.00"

Output JSON:
{
  "comprobante": {
    "tipo_comprobante": "factura", "serie": "F001", "numero": "123",
    "fecha_emision": "2025-07-15", "moneda": "PEN", "monto_total": 900.00, "origen": "electronico"
  },
  "emisor": { "ruc": "20345678901", "razon_social": "COMERCIAL OMEGA SAC", "nombre_comercial": null },
  "items": [
    { "descripcion": "Servicio Contable", "cantidad": 1.0, "precio_unitario": 500.00, "monto_item": 500.00 },
    { "descripcion": "Asesoría Tributaria", "cantidad": 2.0, "precio_unitario": 200.00, "monto_item": 400.00 }
  ],
  "cliente": { "nombre_cliente": "JUAN PEREZ LOPEZ", "doc_cliente": "75524035", "tipo_doc_cliente": "DNI" }
}

RESPONDE ÚNICAMENTE CON EL JSON VÁLIDO.
"""

RECEIPT_SCHEMA = {
  "type": "object",
  "properties": {
    "comprobante": {
      "type": "object",
      "properties": {
        "tipo_comprobante": {"type": "string"},
        "serie": {"type": "string"},
        "numero": {"type": "string"},
        "fecha_emision": {"type": "string"},
        "moneda": {"type": "string"},
        "monto_total": {"type": "number"},
        "origen": {"type": "string"}
      },
      "required": ["tipo_comprobante", "serie", "numero", "fecha_emision", "monto_total"]
    },
    "emisor": {
      "type": "object",
      "properties": {
        "ruc": {"type": "string"},
        "razon_social": {"type": "string"},
        "nombre_comercial": {"type": ["string", "null"]}
      },
      "required": ["ruc", "razon_social"]
    },
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "descripcion": {"type": "string"},
          "cantidad": {"type": "number"},
          "precio_unitario": {"type": "number"},
          "monto_item": {"type": "number"}
        },
        "required": ["descripcion", "cantidad", "precio_unitario", "monto_item"]
      }
    },
    "cliente": {
      "type": "object",
      "properties": {
        "nombre_cliente": {"type": ["string", "null"]},
        "doc_cliente": {"type": ["string", "null"]},
        "tipo_doc_cliente": {"type": ["string", "null"]}
      },
      "required": ["nombre_cliente", "doc_cliente"]
    }
  },
  "required": ["comprobante", "emisor", "items", "cliente"]
}

def query_ollama(model: str, prompt: str, schema: Dict = None) -> Dict:
    url = f"{OLLAMA_HOST}/api/generate"

    # Use schema if provided. If schema is None, use "json" ONLY if explicitly requested, otherwise None (text)
    # But for benchmark we default to json.
    # Let's change logic: if schema is passed, use it. If schema is None, use "json" by default?
    # No, let's make it flexible.

    if schema is not None:
        fmt = schema
    else:
        # If no schema, default to None (text) unless we want to force json
        # For the benchmark loop we pass RECEIPT_SCHEMA, so it will use it.
        # For sanity check we pass None, so we want text.
        fmt = None

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0, # Deterministic
            "seed": 42
        },
    }
    if fmt:
        payload["format"] = fmt

    try:
        t0 = time.perf_counter()
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        dt = time.perf_counter() - t0

        json_resp = resp.json()
        if "response" not in json_resp:
            print(f"DEBUG: No 'response' field in Ollama output: {json_resp.keys()}")

        return {"response": json_resp.get("response", ""), "latency": dt, "error": None}
    except Exception as e:
        print(f"DEBUG: Query Ollama Error: {e}")
        return {"response": "", "latency": 0.0, "error": str(e)}

def normalize_str(s: Any) -> str:
    return str(s).strip().upper()

def calculate_precision(expected: Dict, actual: Dict) -> Dict:
    metrics = {
        "match_ruc": 0,
        "match_serie": 0,
        "match_numero": 0,
        "match_fecha": 0,
        "match_monto": 0,
        "match_items_count": 0
    }

    # Extract from nested structure
    exp_comp = expected.get("comprobante", {})
    exp_emisor = expected.get("emisor", {})
    exp_items = expected.get("items", [])

    act_comp = actual.get("comprobante", {})
    act_emisor = actual.get("emisor", {})
    act_items = actual.get("items", [])

    if normalize_str(exp_emisor.get("ruc")) == normalize_str(act_emisor.get("ruc")):
        metrics["match_ruc"] = 1

    if normalize_str(exp_comp.get("serie")) == normalize_str(act_comp.get("serie")):
        metrics["match_serie"] = 1

    if normalize_str(exp_comp.get("numero")) == normalize_str(act_comp.get("numero")):
        metrics["match_numero"] = 1

    if normalize_str(exp_comp.get("fecha_emision")) == normalize_str(act_comp.get("fecha_emision")):
        metrics["match_fecha"] = 1

    if float(exp_comp.get("monto_total", 0)) == float(act_comp.get("monto_total", 0)):
        metrics["match_monto"] = 1

    if len(exp_items) == len(act_items):
        metrics["match_items_count"] = 1

    return metrics

def run_benchmark(data_path: str, models: List[str]):
    path = pathlib.Path(data_path)
    if not path.exists():
        print(f"Error: Data file {data_path} not found.")
        return

    with open(path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    results = {}

    # Sanity check for the first model
    if models:
        m = models[0]
        print(f"Sanity check for {m}...")
        sanity = query_ollama(m, "Say 'Hello'", schema=None)
        print(f"Sanity response: {sanity}")

    for model in models:
        print(f"Benchmarking model: {model}...")
        model_metrics = {
            "latencies": [],
            "precisions": {
                "ruc": [], "serie": [], "numero": [], "fecha": [], "monto": [], "items": []
            },
            "errors": 0
        }

        for i, record in enumerate(dataset):
            # Construct prompt with Input OCR
            prompt = PROMPT_SISTEMA + f'\nInput OCR:\n"{record["texto_ocr"]}"\n\nOutput JSON:'

            # Pass the schema to enforce structure
            res = query_ollama(model, prompt, schema=RECEIPT_SCHEMA)

            if res["error"]:
                print(f"  Error on sample {i}: {res['error']}")
                model_metrics["errors"] += 1
                continue

            model_metrics["latencies"].append(res["latency"])

            try:
                # Clean up markdown code blocks if present
                clean_json = res["response"].replace("```json", "").replace("```", "").strip()

                # Remove <think> tags if present (common in Qwen/DeepSeek models)
                import re
                clean_json = re.sub(r'<think>.*?</think>', '', clean_json, flags=re.DOTALL).strip()

                parsed_json = json.loads(clean_json)
                print(f"  Sample {i} Output: {json.dumps(parsed_json, indent=2)}")

                prec = calculate_precision(record["campos_esperados"], parsed_json)

                model_metrics["precisions"]["ruc"].append(prec["match_ruc"])
                model_metrics["precisions"]["serie"].append(prec["match_serie"])
                model_metrics["precisions"]["numero"].append(prec["match_numero"])
                model_metrics["precisions"]["fecha"].append(prec["match_fecha"])
                model_metrics["precisions"]["monto"].append(prec["match_monto"])
                model_metrics["precisions"]["items"].append(prec["match_items_count"])

            except json.JSONDecodeError:
                print(f"  JSON Decode Error on sample {i}")
                print(f"  RAW RESPONSE: {res['response'][:500]}...")
                model_metrics["errors"] += 1
            except Exception as e:
                print(f"  Validation Error on sample {i}: {e}")
                model_metrics["errors"] += 1

        # Aggregate results for model
        avg_latency = statistics.mean(model_metrics["latencies"]) if model_metrics["latencies"] else 0
        avg_precisions = {k: (statistics.mean(v) if v else 0) for k, v in model_metrics["precisions"].items()}

        results[model] = {
            "avg_latency_sec": round(avg_latency, 4),
            "precision": {k: round(v, 4) for k, v in avg_precisions.items()},
            "total_samples": len(dataset),
            "failed_samples": model_metrics["errors"]
        }

    print("\n=== BENCHMARK RESULTS ===")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="benchmark/data/synthetic_ocr.json", help="Path to synthetic data JSON")
    parser.add_argument("--models", nargs="+", default=["llama3.1:8b", "gemma3:12b", "gpt-oss:20b"], help="List of Ollama models to test")
    args = parser.parse_args()

    run_benchmark(args.data, args.models)
