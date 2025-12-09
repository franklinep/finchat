from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Emisor
from app.db.repositories.base_repository import BaseRepository


class EmisorRepositorio(BaseRepository[Emisor]):
    def __init__(self, session: Session):
        super().__init__(session)

    def crear(
        self,
        ruc: str,
        razon_social: str,
        nombre_comercial: Optional[str] = None,
        ciiu_principal: Optional[str] = None,
        estado_ruc: Optional[str] = None,
        condicion_ruc: Optional[str] = None,
    ) -> Emisor:
        emisor = Emisor(
            ruc=ruc,
            razon_social=razon_social,
            nombre_comercial=nombre_comercial,
            ciiu_principal=ciiu_principal,
            estado_ruc=estado_ruc,
            condicion_ruc=condicion_ruc,
        )
        self.session.add(emisor)
        return emisor

    def buscar_por_ruc(self, ruc: str) -> Optional[Emisor]:
        stmt = select(Emisor).where(Emisor.ruc == ruc)
        return self.session.scalar(stmt)
