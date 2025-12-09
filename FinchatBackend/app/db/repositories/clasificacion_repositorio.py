from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Clasificacion
from app.db.repositories.base_repository import BaseRepository


class ClasificacionRepositorio(BaseRepository[Clasificacion]):
    def __init__(self, session: Session):
        super().__init__(session)

    def crear(
        self,
        *,
        id_comprobante: int,
        categoria_gasto: str,
        porcentaje_deduccion: float,
        ciiu_utilizado: Optional[str] = None,
        version_regla: str = "v1.0",
        fuente_clasificacion: str = "automatico",
    ) -> Clasificacion:
        clasificacion = Clasificacion(
            id_comprobante=id_comprobante,
            categoria_gasto=categoria_gasto,
            porcentaje_deduccion=porcentaje_deduccion,
            ciiu_utilizado=ciiu_utilizado,
            version_regla=version_regla,
            fuente_clasificacion=fuente_clasificacion,
        )
        self.session.add(clasificacion)
        return clasificacion

    def obtener_por_comprobante(self, id_comprobante: int) -> Optional[Clasificacion]:
        stmt = select(Clasificacion).where(Clasificacion.id_comprobante == id_comprobante)
        return self.session.scalar(stmt)
