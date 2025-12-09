from fastapi import APIRouter, FastAPI
from app.api.v1.routes.health import health_router
from app.api.v1.routes.comprobantes import comprobantes_router
from app.api.v1.routes.auth import auth_router
from app.api.v1.middlewares.auth_middleware import AuthMiddleware

def create_app() -> FastAPI:
    app = FastAPI(title="Finchat Backend API", version="1.0.0")
    app.add_middleware(
        AuthMiddleware,
        public_paths=["/api/v1/auth", "/api/v1/health", "/docs", "/openapi.json"],
    )

    internal_router = APIRouter(prefix="/api/v1")
    # los routers (enrutadores)
    internal_router.include_router(health_router)
    internal_router.include_router(auth_router, tags=["Auth"])
    internal_router.include_router(comprobantes_router, tags=["Comprobantes"])

    # agregamos a la App
    app.include_router(internal_router)

    return app

