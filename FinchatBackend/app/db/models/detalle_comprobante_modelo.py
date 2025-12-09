from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.comprobante_modelo import Comprobante

class DetalleComprobante(Base):
    __tablename__ = "detalle_comprobante"

    id_detalle: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_comprobante: Mapped[int] = mapped_column(
        ForeignKey("comprobante.id_comprobante", ondelete="CASCADE"), nullable=False
    )
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    cantidad: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    precio_unitario: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    monto_item: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))

    comprobante: Mapped["Comprobante"] = relationship("Comprobante", back_populates="detalles")
