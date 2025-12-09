"""Schemas para consultas en lenguaje natural."""

from typing import Optional, List
from pydantic import BaseModel, Field


class ConsultaRequest(BaseModel):
    mensaje: str = Field(..., description="Query en lenguaje natural")


class ConsultaResponse(BaseModel):
    tipo: str = "consulta"
    respuesta: str
    datos: Optional[List[dict]] = None
    totales: Optional[dict] = None
