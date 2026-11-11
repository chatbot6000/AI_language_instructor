"""AI Configuration — endpoint, model, key (server-side only)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import AiConfig, User
from app.schemas import AiConfigOut, AiConfigUpdate

router = APIRouter(prefix="/api/config", tags=["config"])


def _get_or_create_config(db: Session, user: User) -> AiConfig:
    cfg = db.query(AiConfig).filter(AiConfig.user_id == user.id).first()
    if cfg is None:
        cfg = AiConfig(user_id=user.id)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg


def _to_out(cfg: AiConfig) -> AiConfigOut:
    try:
        temp = float(cfg.temperature)
    except (TypeError, ValueError):
        temp = 0.7
    return AiConfigOut(
        base_url=cfg.base_url,
        model=cfg.model,
        temperature=temp,
        has_api_key=bool(cfg.api_key),
        updated_at=cfg.updated_at,
    )


@router.get("/ai", response_model=AiConfigOut)
def get_ai_config(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AiConfigOut:
    return _to_out(_get_or_create_config(db, user))


@router.put("/ai", response_model=AiConfigOut)
def update_ai_config(
    body: AiConfigUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AiConfigOut:
    cfg = _get_or_create_config(db, user)
    cfg.base_url = body.base_url.strip().rstrip("/")
    cfg.model = body.model.strip()
    cfg.temperature = str(body.temperature)
    # api_key: None means leave unchanged; "" clears; otherwise replace
    if body.api_key is not None:
        cfg.api_key = body.api_key.strip()
    db.commit()
    db.refresh(cfg)
    return _to_out(cfg)
