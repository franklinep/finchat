from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.usuario_modelo import Usuario
    from app.db.models.comprobante_modelo import Comprobante

class EstadoTrabajo(Base):
    __tablename__ = "estado_trabajo"

    id_trabajo: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True)
    id_usuario: Mapped[Optional[int]] = mapped_column(
        ForeignKey("usuario.id_usuario"), nullable=True)
    id_comprobante: Mapped[Optional[int]] = mapped_column(
        ForeignKey("comprobante.id_comprobante"), nullable=True)
    tipo_trabajo: Mapped[str] = mapped_column(String(20), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False)
    codigo_error: Mapped[Optional[str]] = mapped_column(String(50))
    intentos: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0")
    mensaje: Mapped[Optional[str]] = mapped_column(Text)

    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="estados_trabajo")
    comprobante: Mapped["Comprobante"] = relationship("Comprobante")
