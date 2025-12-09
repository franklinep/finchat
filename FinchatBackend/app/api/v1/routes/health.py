from fastapi import APIRouter
from sqlalchemy import text

from app.db.sesion import Session

health_router = APIRouter()

@health_router.get("/health", tags=["Health"])
async def health_check():
    session = Session()
    try:
        session.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
    finally:
        session.close()

