from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import OcrPagina
from app.db.repositories.base_repository import BaseRepository


class OcrPaginaRepositorio(BaseRepository[OcrPagina]):
    def __init__(self, session: Session):
        super().__init__(session)

    def crear(
        self,
        *,
        id_comprobante: int,
        numero_pagina: int,
        texto_pagina: Optional[str] = None,
        confianza_promedio: Optional[float] = None,
    ) -> OcrPagina:
        ocr_pagina = OcrPagina(
            id_comprobante=id_comprobante,
            numero_pagina=numero_pagina,
            texto_pagina=texto_pagina,
            confianza_promedio=confianza_promedio,
        )
        self.session.add(ocr_pagina)
        return ocr_pagina

    def listar_por_comprobante(self, id_comprobante: int) -> List[OcrPagina]:
        stmt = (
            select(OcrPagina)
            .where(OcrPagina.id_comprobante == id_comprobante)
            .order_by(OcrPagina.numero_pagina)
        )
        return list(self.session.scalars(stmt).all())
