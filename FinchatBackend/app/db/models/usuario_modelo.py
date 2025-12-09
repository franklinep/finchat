from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.comprobante_modelo import Comprobante
    from app.db.models.estado_trabajo_modelo import EstadoTrabajo
    from app.db.models.historial_chat_modelo import HistorialChat


class Usuario(Base):
    __tablename__ = "usuario"

    id_usuario: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre_mostrar: Mapped[str] = mapped_column(String(120), nullable=False)
    correo_electronico: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, nullable=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)


    comprobantes: Mapped[List["Comprobante"]] = relationship(
        back_populates="usuario"
    )
    estados_trabajo: Mapped[List["EstadoTrabajo"]] = relationship(
        back_populates="usuario"
    )
    historial_chat: Mapped[List["HistorialChat"]] = relationship(
        back_populates="usuario"
    )
