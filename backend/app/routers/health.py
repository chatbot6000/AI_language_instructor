"""Health / hello endpoints for M0 smoke checks."""

from fastapi import APIRouter

from app.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name}


@router.get("/api/hello")
def hello() -> dict:
    return {
        "message": "EVANGELINE is running",
        "product": "Evolving Virtual Assistant for Nurturing Graduated Engagement in Language Immersion Neural Experience",
    }
