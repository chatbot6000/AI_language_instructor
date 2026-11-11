"""
SQLite engine + session factory.

One job: give the rest of the app a DB session and create tables on startup.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import DATA_DIR, settings


# Ensure the data directory exists before opening SQLite
DATA_DIR.mkdir(parents=True, exist_ok=True)

# check_same_thread=False is required for SQLite + FastAPI's thread pool
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yield a request-scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables if they do not exist (fine for M0/M1 prototype)."""
    # Import models so metadata is registered before create_all
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
