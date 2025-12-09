"""Extracción de texto de imágenes usando PaddleOCR con soporte GPU."""

from __future__ import annotations

from functools import lru_cache
from typing import Iterable, Tuple

import numpy as np
from paddleocr import PaddleOCR

from app.config.settings import settings


@lru_cache(maxsize=1)
def _get_ocr() -> PaddleOCR:
    return PaddleOCR(
        lang="es",
        device=settings.device or "cpu",
        use_textline_orientation=True,
    )


def _parse_result(result: Iterable) -> Tuple[list, list]:
    if not result:
        return [], []

    first = result[0]

    # Nueva API: OCRResult
    if hasattr(first, "rec_texts"):
        texts = getattr(first, "rec_texts", []) or []
        scores = getattr(first, "rec_scores", []) or []
        return list(texts), list(scores)

    # Diccionario
    if isinstance(first, dict) and ("rec_texts" in first or "rec_scores" in first):
        texts = first.get("rec_texts") or []
        scores = first.get("rec_scores") or []
        return list(texts), list(scores)

    # API antigua
    if isinstance(first, (list, tuple)):
        texts, scores = [], []
        for line in first:
            if not line or len(line) < 2:
                continue
            text = line[1][0]
            score = line[1][1]
            if text and str(text).strip():
                texts.append(str(text).strip())
                scores.append(score)
        return texts, scores

    return [], []


def extraer_texto_img(ruta_img: str) -> dict:
    ocr = _get_ocr()
    result = ocr.ocr(ruta_img)
    textos, scores = _parse_result(result)

    if scores:
        confianza_promedio = float(np.mean(scores))
    else:
        confianza_promedio = 0.0

    return {
        "texto": "\n".join(textos),
        "confianza_promedio": confianza_promedio,
    }
