from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Validacion
from app.db.repositories.base_repository import BaseRepository


class ValidacionRepositorio(BaseRepository[Validacion]):
    def __init__(self, session: Session):
        super().__init__(session)

    def crear(
        self,
        *,
        id_comprobante: int,
        estado_ruc: Optional[str] = None,
        condicion_ruc: Optional[str] = None,
        ciiu_detectado: Optional[str] = None,
        nombre_comercial_sunat: Optional[str] = None,
        nombre_emisor_ocr: Optional[str] = None,
        coincide_nombre: Optional[bool] = None,
        pasa_reglas: Optional[bool] = False,
        motivo_no_deducible: Optional[str] = None,
    ) -> Validacion:
        validacion = Validacion(
            id_comprobante=id_comprobante,
            estado_ruc=estado_ruc,
            condicion_ruc=condicion_ruc,
            ciiu_detectado=ciiu_detectado,
            nombre_comercial_sunat=nombre_comercial_sunat,
            nombre_emisor_ocr=nombre_emisor_ocr,
            coincide_nombre=coincide_nombre,
            pasa_reglas=pasa_reglas,
            motivo_no_deducible=motivo_no_deducible,
        )
        self.session.add(validacion)
        return validacion

    def obtener_por_comprobante(self, id_comprobante: int) -> Optional[Validacion]:
        stmt = select(Validacion).where(Validacion.id_comprobante == id_comprobante)
        return self.session.scalar(stmt)
