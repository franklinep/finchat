from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Clasificacion(Base):
    __tablename__ = "clasificacion"

    id_comprobante: Mapped[int] = mapped_column(
        ForeignKey("comprobante.id_comprobante", ondelete="CASCADE"),
        primary_key=True,
    )
    categoria_gasto: Mapped[Optional[str]] = mapped_column(String(60))
    porcentaje_deduccion: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    ciiu_utilizado: Mapped[Optional[str]] = mapped_column(String(10))
    fuente_clasificacion: Mapped[Optional[str]] = mapped_column(String(50))
    version_regla: Mapped[str] = mapped_column(String(20), server_default="v1")

    comprobante = relationship("Comprobante", back_populates="clasificacion")
