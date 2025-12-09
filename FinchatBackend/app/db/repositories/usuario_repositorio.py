from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Usuario
from app.db.repositories.base_repository import BaseRepository


class UsuarioRepositorio(BaseRepository[Usuario]):
    def __init__(self, session: Session):
        super().__init__(session)

    def crear(
        self,
        nombre_mostrar: str,
        correo_electronico: Optional[str] = None,
        password_hash: str = "",
    ) -> Usuario:
        usuario = Usuario(
            nombre_mostrar=nombre_mostrar,
            correo_electronico=correo_electronico,
            password_hash=password_hash,
        )
        self.session.add(usuario)
        return usuario

    def buscar_por_correo(self, correo_electronico: str) -> Optional[Usuario]:
        stmt = select(Usuario).where(Usuario.correo_electronico == correo_electronico)
        return self.session.scalar(stmt)
