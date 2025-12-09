import argparse
import json
import time
from typing import List, Dict

from agno.models.ollama import Ollama
from app.config.settings import settings


PROMPT = "Extrae RUC, serie, numero, fecha y monto total del siguiente texto:\n{texto}"


def medir_modelo(model_id: str, texto: str) -> Dict:
    model = Ollama(
        id=model_id,
        host=settings.ollama_host,
        options={"temperature": 0, "seed": 123},
    )
    t0 = time.perf_counter()
    resp = model.complete(PROMPT.format(texto=texto))
    dt = time.perf_counter() - t0
    return {"modelo": model_id, "latencia_s": dt, "tokens_aprox": len(resp.split())}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelos", nargs="+", required=True, help="IDs de modelos en Ollama (ej: 8b 12b 20b)")
    ap.add_argument("--texto", required=True, help="Texto OCR a evaluar")
    args = ap.parse_args()

    resultados: List[Dict] = [medir_modelo(m, args.texto) for m in args.modelos]
    print(json.dumps(resultados, indent=2))


if __name__ == "__main__":
    main()
