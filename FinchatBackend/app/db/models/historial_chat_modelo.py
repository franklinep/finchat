from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.usuario_modelo import Usuario

class HistorialChat(Base):
    __tablename__ = "historial_chat"

    id_mensaje: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_usuario: Mapped[Optional[int]] = mapped_column(
        ForeignKey("usuario.id_usuario"), nullable=True)
    rol: Mapped[str] = mapped_column(String(20), nullable=False)
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False)


    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="historial_chat")
