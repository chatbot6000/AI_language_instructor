"""
Spanish text chat — M1 vertical slice.

Creates/reuses a session, persists messages, calls LLMClient (or stub).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.llm_client import build_spanish_messages, chat_completion
from app.models import AiConfig, ChatSession, Message, User
from app.schemas import ChatRequest, ChatResponse, MessageOut, SessionOut

router = APIRouter(prefix="/api/chat", tags=["chat"])

ACTIVE_LANGUAGE = "es"  # M1: Spanish only; Japanese arrives in M5


def _active_session(db: Session, user: User) -> ChatSession | None:
    """Most recent open Spanish session for this user (ended_at is null)."""
    return (
        db.query(ChatSession)
        .filter(
            ChatSession.user_id == user.id,
            ChatSession.language == ACTIVE_LANGUAGE,
            ChatSession.ended_at.is_(None),
        )
        .order_by(ChatSession.id.desc())
        .first()
    )


def _ensure_session(db: Session, user: User, session_id: int | None) -> ChatSession:
    if session_id is not None:
        session = (
            db.query(ChatSession)
            .filter(ChatSession.id == session_id, ChatSession.user_id == user.id)
            .first()
        )
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return session

    existing = _active_session(db, user)
    if existing:
        return existing

    session = ChatSession(user_id=user.id, language=ACTIVE_LANGUAGE)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def _history_for_llm(session: ChatSession) -> list[dict[str, str]]:
    return [
        {"role": m.role, "content": m.text}
        for m in session.messages
        if m.role in ("user", "assistant")
    ]


def _message_out(m: Message) -> MessageOut:
    return MessageOut(
        id=m.id,
        role=m.role,
        text=m.text,
        display_text=m.display_text or m.text,
        created_at=m.created_at,
    )


@router.get("/session", response_model=SessionOut)
def get_or_create_session(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SessionOut:
    """Return the active Spanish session (create empty one if needed) + messages."""
    session = _ensure_session(db, user, None)
    db.refresh(session)
    return SessionOut(
        id=session.id,
        language=session.language,
        started_at=session.started_at,
        ended_at=session.ended_at,
        summary=session.summary,
        messages=[_message_out(m) for m in session.messages],
    )


@router.post("/message", response_model=ChatResponse)
async def send_message(
    body: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatResponse:
    session = _ensure_session(db, user, body.session_id)
    text = body.message.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Empty message")

    user_msg = Message(
        session_id=session.id,
        role="user",
        text=text,
        display_text=text,
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)
    db.refresh(session)

    cfg = db.query(AiConfig).filter(AiConfig.user_id == user.id).first()
    base_url = cfg.base_url if cfg else ""
    model = cfg.model if cfg else ""
    api_key = cfg.api_key if cfg else ""
    try:
        temperature = float(cfg.temperature) if cfg else 0.7
    except (TypeError, ValueError):
        temperature = 0.7

    llm_messages = build_spanish_messages(_history_for_llm(session)[:-1], text)
    result = await chat_completion(
        base_url=base_url,
        model=model,
        api_key=api_key,
        temperature=temperature,
        messages=llm_messages,
    )

    assistant_msg = Message(
        session_id=session.id,
        role="assistant",
        text=result.text,
        display_text=result.text,
        meta_json='{"mocked": true}' if result.mocked else None,
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return ChatResponse(
        session_id=session.id,
        user_message=_message_out(user_msg),
        assistant_message=_message_out(assistant_msg),
        mocked=result.mocked,
    )


@router.post("/session/new", response_model=SessionOut)
def start_new_session(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SessionOut:
    """Close the open session (if any) and start a fresh Spanish session."""
    from datetime import datetime, timezone

    current = _active_session(db, user)
    if current:
        current.ended_at = datetime.now(timezone.utc)
        db.commit()

    session = ChatSession(user_id=user.id, language=ACTIVE_LANGUAGE)
    db.add(session)
    db.commit()
    db.refresh(session)
    return SessionOut(
        id=session.id,
        language=session.language,
        started_at=session.started_at,
        ended_at=session.ended_at,
        summary=session.summary,
        messages=[],
    )
