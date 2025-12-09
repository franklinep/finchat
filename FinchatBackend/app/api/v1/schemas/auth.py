from typing import Optional

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    nombre_mostrar: str
    correo_electronico: EmailStr
    password: str


class LoginRequest(BaseModel):
    correo_electronico: EmailStr
    password: str


class UsuarioOut(BaseModel):
    id_usuario: int
    nombre_mostrar: str
    correo_electronico: Optional[EmailStr] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
