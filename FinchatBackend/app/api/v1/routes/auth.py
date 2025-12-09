from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UsuarioOut,
)
from app.db.sesion import get_db
from app.features.auth import AuthService

auth_router = APIRouter()


@auth_router.post("/auth/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    try:
        usuario, token = service.registrar_usuario(
            nombre_mostrar=payload.nombre_mostrar,
            correo_electronico=payload.correo_electronico,
            password=payload.password,
        )
        print("Usuario registrado: ", UsuarioOut.model_validate(usuario))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return TokenResponse(access_token=token)


@auth_router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    try:
        usuario, token = service.login(
            correo_electronico=payload.correo_electronico,
            password=payload.password,
        )
        print("Usuario logueado: ", UsuarioOut.model_validate(usuario))
    except ValueError:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    return TokenResponse(access_token=token)
