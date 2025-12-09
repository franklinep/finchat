import argparse
import asyncio
import json
import pathlib
import time
from typing import Tuple

from app.db.sesion import get_db
from app.features.agents.pipeline_ingesta import IngestaWorkflow
from app.config.settings import settings


async def procesa_archivo(wf: IngestaWorkflow, usuario_id: int, archivo: pathlib.Path) -> Tuple[dict, float]:
    contenido = archivo.read_bytes()
    mime = "application/pdf" if archivo.suffix.lower() == ".pdf" else "image/jpeg"
    t0 = time.perf_counter()
    res = await wf.run(
        {
            "usuario_id": usuario_id,
            "nombre_archivo": archivo.name,
            "mime_type": mime,
            "contenido": contenido,
        }
    )
    dt = time.perf_counter() - t0
    return res, dt


async def main_async(args) -> None:
    if args.modelo:
        settings.ollama_model = args.modelo

    archivos = [
        p for p in sorted(pathlib.Path(args.carpeta).iterdir())
        if p.is_file() and p.suffix.lower() in {".pdf", ".jpg", ".jpeg", ".png", ".bmp"}
    ]
    db = next(get_db())
    wf = IngestaWorkflow(db)

    latencias = []
    duplicados = 0
    exitos = 0

    for arch in archivos:
        res, dt = await procesa_archivo(wf, args.usuario, arch)
        latencias.append(dt)
        if res.get("duplicado"):
            duplicados += 1
        if res.get("exito"):
            exitos += 1

    latencias_sorted = sorted(latencias)
    p95 = latencias_sorted[int(0.95 * len(latencias)) - 1] if latencias_sorted else 0
    throughput = len(latencias) / sum(latencias) if latencias else 0

    print(
        json.dumps(
            {
                "modelo": settings.ollama_model,
                "archivos": len(archivos),
                "exitos": exitos,
                "duplicados": duplicados,
                "latencia_promedio_s": sum(latencias) / len(latencias) if latencias else 0,
                "latencia_p95_s": p95,
                "throughput_arch_s": throughput,
            },
            indent=2,
        )
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--carpeta", required=True, help="Carpeta con comprobantes de prueba")
    ap.add_argument("--usuario", type=int, default=1, help="ID de usuario de prueba")
    ap.add_argument("--modelo", help="ID de modelo en Ollama (ej: gpt-oss:20b, gemma3:12b, llama3.1:8b)")
    args = ap.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
