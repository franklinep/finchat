from __future__ import annotations

from typing import Tuple

from sqlalchemy.orm import Session

from app.config.settings import Settings
from app.db.models import Usuario
from app.db.repositories.usuario_repositorio import UsuarioRepositorio
from app.utils.auth import decode_jwt, encode_jwt, hash_password, verify_password


class AuthService:
    def __init__(self, session: Session, settings: Settings | None = None):
        self.session = session
        self.repo = UsuarioRepositorio(session)
        self.settings = settings or Settings()

    def registrar_usuario(
        self, nombre_mostrar: str, correo_electronico: str, password: str
    ) -> Tuple[Usuario, str]:
        existente = self.repo.buscar_por_correo(correo_electronico)
        if existente:
            raise ValueError("El correo ya está registrado")
        password_hash = hash_password(password)
        usuario = self.repo.crear(
            nombre_mostrar=nombre_mostrar,
            correo_electronico=correo_electronico,
            password_hash=password_hash,
        )
        self.session.commit()
        token = self._emitir_token(usuario)
        return usuario, token

    def login(self, correo_electronico: str, password: str) -> Tuple[Usuario, str]:
        usuario = self.repo.buscar_por_correo(correo_electronico)
        if not usuario or not verify_password(password, usuario.password_hash):
            raise ValueError("Credenciales inválidas")
        token = self._emitir_token(usuario)
        return usuario, token

    def _emitir_token(self, usuario: Usuario) -> str:
        return encode_jwt(
            {"sub": usuario.id_usuario, "email": usuario.correo_electronico},
            secret=self.settings.jwt_secret,
            expires_minutes=self.settings.jwt_expire_minutes,
        )

    def verificar_token(self, token: str):
        return decode_jwt(token, self.settings.jwt_secret)
