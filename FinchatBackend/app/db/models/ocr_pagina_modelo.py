from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.comprobante_modelo import Comprobante

class OcrPagina(Base):
    __tablename__ = "ocr_pagina"
    __table_args__ = (
        UniqueConstraint(
            "id_comprobante",
            "numero_pagina",
            name="idx_ocr_pagina_comprobante_pagina",
        ),
    )

    id_ocr_pagina: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_comprobante: Mapped[int] = mapped_column(
        ForeignKey("comprobante.id_comprobante", ondelete="CASCADE"), nullable=False)
    numero_pagina: Mapped[int] = mapped_column(nullable=False, default=1)
    texto_pagina: Mapped[Optional[str]] = mapped_column(Text)
    confianza_promedio: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))

    comprobante: Mapped["Comprobante"] = relationship("Comprobante", back_populates="ocr_paginas")
