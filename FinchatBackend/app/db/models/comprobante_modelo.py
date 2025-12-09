from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import (
    CHAR,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


if TYPE_CHECKING:
    from app.db.models.usuario_modelo import Usuario
    from app.db.models.emisor_modelo import Emisor
    from app.db.models.detalle_comprobante_modelo import DetalleComprobante
    from app.db.models.validacion_modelo import Validacion
    from app.db.models.clasificacion_modelo import Clasificacion
    from app.db.models.ocr_pagina_modelo import OcrPagina

class Comprobante(Base):
    __tablename__ = "comprobante"
    __table_args__ = (
        UniqueConstraint(
            "id_usuario",
            "id_emisor",
            "serie",
            "numero",
            name="comprobante_unq_usuario_emisor_serie_numero",
        ),
        UniqueConstraint("id_usuario", "hash_archivo", name="comprobante_unq_usuario_hash"),
    )

    id_comprobante: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_usuario: Mapped[Optional[int]] = mapped_column(
        ForeignKey("usuario.id_usuario"), nullable=True)
    id_emisor: Mapped[Optional[int]] = mapped_column(
        ForeignKey("emisor.id_emisor"), nullable=True)
    tipo_comprobante: Mapped[str] = mapped_column(String(10), nullable=False)
    serie: Mapped[str] = mapped_column(String(8), nullable=False)
    numero: Mapped[str] = mapped_column(String(20), nullable=False)
    fecha_emision: Mapped[date] = mapped_column(Date, nullable=False)
    monto_total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    moneda: Mapped[str] = mapped_column(
        CHAR(3),
        nullable=False,
        server_default="PEN")
    origen: Mapped[str] = mapped_column(String(15), nullable=False)
    hash_archivo: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    estado_procesamiento: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="pendiente")
    es_deducible: Mapped[Optional[bool]] = mapped_column(Boolean)
    es_duplicado: Mapped[bool] = mapped_column(Boolean, default=False,
        server_default="false",
        nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True),
        server_default=func.now(),
        nullable=False)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False)
    ruta_archivo: Mapped[Optional[str]] = mapped_column(Text)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100))


    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="comprobantes")
    emisor: Mapped["Emisor"] = relationship("Emisor", back_populates="comprobantes")
    detalles: Mapped[List["DetalleComprobante"]] = relationship(
        back_populates="comprobante", cascade="all, delete-orphan"
    )
    validacion: Mapped[Optional["Validacion"]] = relationship(
        back_populates="comprobante", cascade="all, delete-orphan", uselist=False
    )
    clasificacion: Mapped[Optional["Clasificacion"]] = relationship(
        back_populates="comprobante", cascade="all, delete-orphan", uselist=False
    )
    ocr_paginas: Mapped[List["OcrPagina"]] = relationship(
        back_populates="comprobante", cascade="all, delete-orphan"
    )
