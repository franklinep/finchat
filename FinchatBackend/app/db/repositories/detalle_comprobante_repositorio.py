from __future__ import annotations

from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import DetalleComprobante
from app.db.repositories.base_repository import BaseRepository


class DetalleComprobanteRepositorio(BaseRepository[DetalleComprobante]):
    def __init__(self, session: Session):
        super().__init__(session)

    def crear(
        self,
        *,
        id_comprobante: int,
        descripcion: str,
        cantidad: float = 1.0,
        precio_unitario: float = 0.0,
        monto_item: float,
    ) -> DetalleComprobante:
        detalle = DetalleComprobante(
            id_comprobante=id_comprobante,
            descripcion=descripcion,
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            monto_item=monto_item,
        )
        self.session.add(detalle)
        return detalle

    def listar_por_comprobante(self, id_comprobante: int) -> List[DetalleComprobante]:
        stmt = select(DetalleComprobante).where(
            DetalleComprobante.id_comprobante == id_comprobante
        )
        return list(self.session.scalars(stmt).all())
