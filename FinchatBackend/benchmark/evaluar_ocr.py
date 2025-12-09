import argparse
import json
import pathlib
import statistics
import difflib
from typing import Dict, Tuple, List

from app.features.agents.agente_parseador import AgenteParseador
from app.features.agents.pipeline_context import PipelineContext
from app.libs.ocr.imagen_ocr import extraer_texto_img
from app.libs.ocr.pdf_extractor import extraer_texto_pdf


def _cer(ref: str, hyp: str) -> float:
    """Character Error Rate simple usando difflib."""
    if not ref and not hyp:
        return 0.0
    sm = difflib.SequenceMatcher(None, ref, hyp)
    ops = sum(size for tag, _, _, _, size in sm.get_opcodes() if tag != "equal")
    return ops / max(1, len(ref))


def _wer(ref: str, hyp: str) -> float:
    """Word Error Rate aproximado (difflib sobre palabras)."""
    ref_words = ref.split()
    hyp_words = hyp.split()
    sm = difflib.SequenceMatcher(None, ref_words, hyp_words)
    ops = sum(size for tag, _, _, _, size in sm.get_opcodes() if tag != "equal")
    return ops / max(1, len(ref_words)) if ref_words else 0.0


def cargar_labels(path: pathlib.Path) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extraer_texto(path: pathlib.Path) -> Tuple[str, float]:
    if path.suffix.lower() == ".pdf":
        paginas = extraer_texto_pdf(str(path))
        texto = "\n".join(p["texto"] for p in paginas)
        conf = 1.0
    else:
        res = extraer_texto_img(str(path))
        texto = res.get("texto", "")
        conf = res.get("confianza_promedio", 0.0)
    return texto, conf


def parsear_campos(path: pathlib.Path, contenido: bytes, mime: str) -> Dict:
    ctx = PipelineContext(usuario_id=0, nombre_archivo=path.name, mime_type=mime)
    parseador = AgenteParseador(ctx)
    parsed = parseador.parsear_archivo(contenido, mime, path.name)
    return parsed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True, help="Carpeta con archivos y labels.json")
    ap.add_argument("--usar-parseador", action="store_true", help="Evalúa campos usando AgenteParseador (LLM)")
    args = ap.parse_args()

    base = pathlib.Path(args.dataset)
    labels = cargar_labels(base / "labels.json")

    metricas: Dict[str, List[float]] = {
        "cer": [], "wer": [], "confianza": [],
        "acc_ruc": [], "acc_serie": [], "acc_numero": [], "acc_fecha": [], "acc_monto": [], "acc_items": [],
    }

    for nombre, gt in labels.items():
        archivo = base / nombre
        texto, conf = extraer_texto(archivo)
        contenido = archivo.read_bytes()
        metricas["confianza"].append(conf)
        metricas["cer"].append(_cer(gt.get("texto_completo", ""), texto))
        metricas["wer"].append(_wer(gt.get("texto_completo", ""), texto))

        if args.usar_parseador:
            mime = "application/pdf" if archivo.suffix.lower() == ".pdf" else "image/jpeg"
            pred = parsear_campos(archivo, contenido, mime)
            campos_pred = pred.get("comprobante", {})
            emisor_pred = pred.get("emisor", {})
            items_pred = pred.get("items", []) or []
            campos_gt = gt.get("campos_esperados", {})

            metricas["acc_ruc"].append(1 if str(campos_gt.get("ruc_emisor", "")).strip() == str(emisor_pred.get("ruc", "")).strip() else 0)
            metricas["acc_serie"].append(1 if str(campos_gt.get("serie", "")).strip().upper() == str(campos_pred.get("serie", "")).strip().upper() else 0)
            metricas["acc_numero"].append(1 if str(campos_gt.get("numero", "")).strip() == str(campos_pred.get("numero", "")).strip() else 0)
            metricas["acc_fecha"].append(1 if str(campos_gt.get("fecha_emision", "")).strip() == str(campos_pred.get("fecha_emision", "")).strip() else 0)
            metricas["acc_monto"].append(1 if str(campos_gt.get("monto_total", "")).strip() == str(campos_pred.get("monto_total", "")).strip() else 0)
            metricas["acc_items"].append(1 if len(items_pred) == len(campos_gt.get("items", [])) else 0)

    def prom(xs: List[float]) -> float:
        return statistics.mean(xs) if xs else 0.0

    resumen = {k: prom(v) for k, v in metricas.items()}
    print(json.dumps(resumen, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
