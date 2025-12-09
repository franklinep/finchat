from __future__ import annotations

from datetime import date
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Comprobante
from app.db.repositories.base_repository import BaseRepository


class ComprobanteRepositorio(BaseRepository[Comprobante]):
    def __init__(self, session: Session):
        super().__init__(session)

    def crear(
        self,
        *,
        id_usuario: Optional[int],
        id_emisor: Optional[int],
        tipo_comprobante: str,
        serie: str,
        numero: str,
        fecha_emision: date,
        monto_total: float,
        moneda: str,
        origen: str,
        hash_archivo: str,
        estado_procesamiento: str = "pendiente",
        es_deducible: Optional[bool] = None,
        es_duplicado: bool = False,
        ruta_archivo: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> Comprobante:
        comprobante = Comprobante(
            id_usuario=id_usuario,
            id_emisor=id_emisor,
            tipo_comprobante=tipo_comprobante,
            serie=serie,
            numero=numero,
            fecha_emision=fecha_emision,
            monto_total=monto_total,
            moneda=moneda,
            origen=origen,
            hash_archivo=hash_archivo,
            estado_procesamiento=estado_procesamiento,
            es_deducible=es_deducible,
            es_duplicado=es_duplicado,
            ruta_archivo=ruta_archivo,
            mime_type=mime_type,
        )
        self.session.add(comprobante)
        return comprobante

    def buscar_por_hash(self, id_usuario: Optional[int], hash_archivo: str) -> Optional[Comprobante]:
        stmt = select(Comprobante).where(
            Comprobante.id_usuario == id_usuario, Comprobante.hash_archivo == hash_archivo
        )
        return self.session.scalar(stmt)

    def buscar_por_emisor_serie_numero(
        self, id_usuario: Optional[int], id_emisor: int, serie: str, numero: str
    ) -> Optional[Comprobante]:
        stmt = select(Comprobante).where(
            Comprobante.id_usuario == id_usuario,
            Comprobante.id_emisor == id_emisor,
            Comprobante.serie == serie,
            Comprobante.numero == numero,
        )
        return self.session.scalar(stmt)

    def listar_por_usuario(self, id_usuario: int) -> List[Comprobante]:
        stmt = select(Comprobante).where(Comprobante.id_usuario == id_usuario)
        return list(self.session.scalars(stmt).all())
