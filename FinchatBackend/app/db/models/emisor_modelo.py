from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import CHAR, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.comprobante_modelo import Comprobante

class Emisor(Base):
    __tablename__ = "emisor"

    id_emisor: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ruc: Mapped[str] = mapped_column(CHAR(11), unique=True, nullable=False)
    razon_social: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre_comercial: Mapped[Optional[str]] = mapped_column(String(255))
    ciiu_principal: Mapped[Optional[str]] = mapped_column(String(10))
    estado_ruc: Mapped[Optional[str]] = mapped_column(String(30))
    condicion_ruc: Mapped[Optional[str]] = mapped_column(String(30))

    comprobantes: Mapped[List["Comprobante"]] = relationship(
        back_populates="emisor"
    )
