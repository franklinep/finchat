from datetime import date
from typing import List, Optional

from pydantic import BaseModel

# d: schemas para la ingesta de multiples comprobantes
class CamposClave(BaseModel):
    ruc_emisor: Optional[str] = None
    serie_numero: Optional[str] = None
    fecha_emision: Optional[date] = None
    moneda: Optional[str] = None
    monto_total: Optional[float] = None
    nombre_cliente: Optional[str] = None
    doc_cliente: Optional[str] = None
    tipo_comprobante: Optional[str] = None


class ValidacionSunatOut(BaseModel):
    ruc: str
    estadoRuc: Optional[str] = None
    condicionRuc: Optional[str] = None
    ciiuPrincipal: Optional[str] = None
    pasaReglasBasicas: Optional[bool] = None
    motivoNoDeducible: Optional[str] = None


class ClasificacionOut(BaseModel):
    categoriaGasto: str
    porcentajeDeduccion: float
    versionRegla: str


class ArchivoProcesadoOut(BaseModel):
    nombreArchivo: str
    hashArchivo: Optional[str] = None
    esDuplicado: bool
    idComprobante: Optional[int] = None
    camposClave: Optional[CamposClave] = None
    validacionSunat: Optional[ValidacionSunatOut] = None
    clasificacion: Optional[ClasificacionOut] = None

# main response schema para la subida de multiples comprobantes
class SubirComprobantesResponse(BaseModel):
    usuarioId: int
    totalArchivos: int
    procesados: List[ArchivoProcesadoOut]



# d: schema para la API de comprobantes individual
class ComprobanteResumen(BaseModel):
    id_comprobante: int
    fecha_emision: Optional[date]
    serie: Optional[str]
    numero: Optional[str]
    monto_total: Optional[float]
    moneda: Optional[str]
    estado_procesamiento: Optional[str]

    class Config:
        from_attributes = True


class ExtraccionRequest(BaseModel):
    ruta: str
    mime_type: str


class CrearComprobanteRequest(BaseModel):
    ruc_emisor: Optional[str]
    razon_social: Optional[str]
    nombre_comercial: Optional[str]
    tipo_comprobante: str
    serie: str
    numero: str
    fecha_emision: date
    monto_total: float
    moneda: str
    origen: str
    hash_archivo: str
    ruta_archivo: Optional[str] = None
    mime_type: Optional[str] = None
