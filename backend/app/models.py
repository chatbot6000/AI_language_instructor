"""
SQLAlchemy models for M0/M1.

M2+ entities (SrsItem, CurriculumItem, rich LanguageProgress) are stubbed
lightly or omitted — see build plan §6.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    """Learner account (username/password)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    # Optional JSON blob for future prefs (avatar, etc.)
    settings_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    sessions: Mapped[list["ChatSession"]] = relationship(back_populates="user")
    ai_config: Mapped["AiConfig | None"] = relationship(
        back_populates="user", uselist=False
    )


class AiConfig(Base):
    """
    Per-user OpenAI-compatible LLM settings.

    API key is stored server-side only — never returned to the browser in full.
    """

    __tablename__ = "ai_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    base_url: Mapped[str] = mapped_column(
        String(512), default="http://127.0.0.1:11434/v1"
    )
    model: Mapped[str] = mapped_column(String(128), default="llama3.2")
    # Empty string means "no key" (typical for local Ollama)
    api_key: Mapped[str] = mapped_column(String(512), default="")
    temperature: Mapped[str] = mapped_column(String(16), default="0.7")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    user: Mapped["User"] = relationship(back_populates="ai_config")


class ChatSession(Base):
    """One tutoring conversation (M1: Spanish text-only)."""

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    language: Mapped[str] = mapped_column(String(8), default="es")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="sessions")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="session", order_by="Message.id"
    )


class Message(Base):
    """Single turn in a chat session."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))  # user | assistant | system
    text: Mapped[str] = mapped_column(Text)
    # display_text reserved for future romaji / dual-script (M3/M5)
    display_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    meta_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    session: Mapped["ChatSession"] = relationship(back_populates="messages")
