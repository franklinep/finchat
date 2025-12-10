"""
Compara múltiples modelos de Ollama (AgenteParseador) sobre un dataset con labels.

Para cada modelo:
- Recorre los archivos del dataset (PDF/imagen)
- Ejecuta el parseador (LLM) y mide tiempo por archivo
- Calcula exactitud por campo vs campos_esperados en labels.json
- Reporta promedios de acc_* y latencia promedio

Uso:
  python -m benchmark.compare_models_parseador --dataset benchmark/data/eval --modelos gpt-oss:20b gemma3:12b llama3.1:8b
"""

import argparse
import json
import pathlib
import statistics
import time
from typing import Dict, List, Tuple

from app.config.settings import settings
from app.features.agents.agente_parseador import AgenteParseador
from app.features.agents.pipeline_context import PipelineContext


def parsear_campos(path: pathlib.Path, contenido: bytes, mime: str) -> Tuple[Dict, float]:
    ctx = PipelineContext(usuario_id=0, nombre_archivo=path.name, mime_type=mime)
    parseador = AgenteParseador(ctx)
    t0 = time.perf_counter()
    parsed = parseador.parsear_archivo(contenido, mime, path.name)
    dt = time.perf_counter() - t0
    return parsed, dt


def acc(v_gt, v_pred) -> float:
    return 1.0 if str(v_gt).strip() == str(v_pred).strip() else 0.0


def evaluar_modelo(model_id: str, archivos: List[pathlib.Path], labels: Dict) -> Dict:
    settings.ollama_model = model_id
    metricas = {
        "acc_ruc": [], "acc_serie": [], "acc_numero": [], "acc_fecha": [], "acc_monto": [], "acc_items": [], "latencia_s": []
    }
    for archivo in archivos:
        nombre = archivo.name
        if nombre not in labels:
            continue
        gt = labels[nombre]
        campos_gt = gt.get("campos_esperados", {})
        mime = "application/pdf" if archivo.suffix.lower() == ".pdf" else "image/jpeg"
        parsed, dt = parsear_campos(archivo, archivo.read_bytes(), mime)
        comp_pred = parsed.get("comprobante", {})
        emisor_pred = parsed.get("emisor", {})
        items_pred = parsed.get("items", []) or []

        metricas["latencia_s"].append(dt)
        metricas["acc_ruc"].append(acc(campos_gt.get("ruc_emisor", ""), emisor_pred.get("ruc", "")))
        metricas["acc_serie"].append(acc(str(campos_gt.get("serie", "")).upper(), str(comp_pred.get("serie", "")).upper()))
        metricas["acc_numero"].append(acc(campos_gt.get("numero", ""), comp_pred.get("numero", "")))
        metricas["acc_fecha"].append(acc(campos_gt.get("fecha_emision", ""), comp_pred.get("fecha_emision", "")))
        metricas["acc_monto"].append(acc(campos_gt.get("monto_total", ""), comp_pred.get("monto_total", "")))
        metricas["acc_items"].append(acc(len(campos_gt.get("items", [])), len(items_pred)))

    def prom(xs: List[float]) -> float:
        return statistics.mean(xs) if xs else 0.0

    return {
        "modelo": model_id,
        "archivos": len(metricas["latencia_s"]),
        "latencia_prom_s": prom(metricas["latencia_s"]),
        "acc_ruc": prom(metricas["acc_ruc"]),
        "acc_serie": prom(metricas["acc_serie"]),
        "acc_numero": prom(metricas["acc_numero"]),
        "acc_fecha": prom(metricas["acc_fecha"]),
        "acc_monto": prom(metricas["acc_monto"]),
        "acc_items": prom(metricas["acc_items"]),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True, help="Carpeta con archivos y labels.json (o archivo indicado)")
    ap.add_argument("--labels", help="Ruta al archivo de labels (por defecto, labels.json dentro del dataset)")
    ap.add_argument("--modelos", nargs="+", required=True, help="IDs de modelos en Ollama (ej: gpt-oss:20b gemma3:12b llama3.1:8b)")
    args = ap.parse_args()

    base = pathlib.Path(args.dataset)
    labels_path = pathlib.Path(args.labels) if args.labels else (base / "labels.json")
    labels = json.loads(labels_path.read_text(encoding="utf-8"))
    archivos = [
        p for p in sorted(base.iterdir())
        if p.is_file() and p.suffix.lower() in {".pdf", ".jpg", ".jpeg", ".png", ".bmp"}
    ]

    resultados = [evaluar_modelo(m, archivos, labels) for m in args.modelos]
    print(json.dumps(resultados, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
