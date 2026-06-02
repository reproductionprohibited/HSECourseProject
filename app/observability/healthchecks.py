from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.db.engine import sync_session

router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.get("/ready")
def ready():
    try:
        with sync_session() as session:
            session.exec(select(1))
        return {"status": "ok"}
    except Exception:
        raise HTTPException(status_code=503, detail={"status": "not ready"})
