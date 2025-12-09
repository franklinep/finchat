from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

class ComprobanteData(BaseModel):
    """Datos del comprobante para tabla comprobante."""
    tipo_comprobante: str = Field(..., description="Tipo: boleta, factura, etc.")
    serie: str = Field(..., description="Serie del comprobante")
    numero: str = Field(..., description="Número del comprobante")
    fecha_emision: str = Field(..., description="Fecha en formato YYYY-MM-DD")
    moneda: str = Field(default="PEN", description="Moneda: PEN, USD, etc.")
    monto_total: float = Field(..., description="Monto total del comprobante")
    origen: str = Field(default="electronico", description="Origen: electronico o fisico")


class EmisorData(BaseModel):
    """Datos del emisor para tabla emisor."""
    ruc: str = Field(..., description="RUC de 11 dígitos del emisor")
    razon_social: str = Field(..., description="Razón social del emisor")
    nombre_comercial: Optional[str] = Field(None, description="Nombre comercial (si aparece)")


class ItemData(BaseModel):
    """Datos de un ítem para tabla detalle_comprobante."""
    descripcion: str = Field(default="", description="Descripción del producto/servicio")
    cantidad: float = Field(default=1.0, description="Cantidad")
    precio_unitario: float = Field(default=0.0, description="Precio unitario")
    monto_item: float = Field(..., description="Monto total del ítem")

    @field_validator('descripcion', mode='before')
    @classmethod
    def handle_none_descripcion(cls, v):
        return v if v is not None else ""


class ClienteData(BaseModel):
    """Datos del cliente (si aparece en el comprobante)."""
    nombre_cliente: Optional[str] = Field(None, description="Nombre del cliente")
    doc_cliente: Optional[str] = Field(None, description="DNI o RUC del cliente")
    tipo_doc_cliente: Optional[str] = Field(None, description="Tipo: DNI, RUC, etc.")


class ComprobanteParsed(BaseModel):
    """Resultado completo del parsing con datos para todas las tablas."""
    comprobante: ComprobanteData
    emisor: EmisorData
    items: List[ItemData] = Field(description="Lista de ítems del detalle")
    cliente: ClienteData = Field(default_factory=ClienteData)
    confianza_parsing: float = Field(default=0.0, description="Confianza del parsing (0-1)")
    texto_completo_ocr: str = Field(default="", description="Texto completo extraído por OCR")
