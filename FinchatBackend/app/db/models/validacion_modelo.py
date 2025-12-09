from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.comprobante_modelo import Comprobante

class Validacion(Base):
    __tablename__ = "validacion"

    id_comprobante: Mapped[int] = mapped_column(
        ForeignKey("comprobante.id_comprobante", ondelete="CASCADE"),
        primary_key=True,
    )
    estado_ruc: Mapped[Optional[str]] = mapped_column(String(30))
    condicion_ruc: Mapped[Optional[str]] = mapped_column(String(30))
    ciiu_detectado: Mapped[Optional[str]] = mapped_column(String(10))
    nombre_comercial_sunat: Mapped[Optional[str]] = mapped_column(String(255))
    nombre_emisor_ocr: Mapped[Optional[str]] = mapped_column(String(255))
    coincide_nombre: Mapped[Optional[bool]] = mapped_column(Boolean)
    pasa_reglas: Mapped[Optional[bool]] = mapped_column(Boolean)
    motivo_no_deducible: Mapped[Optional[str]] = mapped_column(Text)

    comprobante: Mapped["Comprobante"] = relationship("Comprobante", back_populates="validacion")
