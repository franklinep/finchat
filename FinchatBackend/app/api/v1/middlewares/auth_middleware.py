from __future__ import annotations

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.config.settings import Settings
from app.utils.auth import decode_jwt


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, public_paths: list[str] | None = None):
        super().__init__(app)
        self.settings = Settings()
        self.public_paths = public_paths or ["/api/v1/auth", "/api/v1/health"]

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        if any(path.startswith(p) for p in self.public_paths):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.lower().startswith("bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header Bearer requerido",
            )

        token = auth_header.split(" ", 1)[1]
        payload = decode_jwt(token, self.settings.jwt_secret)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado",
            )

        # p: adjuntar payload al scope para uso posterior
        request.state.user = payload
        return await call_next(request)
