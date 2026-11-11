"""
App-level settings loaded from environment variables.

User-editable LLM settings (base URL, model, API key) live in the DB
via the Config UI — not here. This module only holds process defaults.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# backend/app/config.py → backend/
BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data"
DEFAULT_DB_PATH = DATA_DIR / "evangeline.db"


class Settings(BaseSettings):
    """Process configuration (env / .env)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "EVANGELINE"
    # Secret for signing JWTs — override in production via EVANGELINE_SECRET_KEY
    secret_key: str = "dev-only-change-me-evangeline"
    access_token_expire_minutes: int = 60 * 24 * 7  # one week for local use
    database_url: str = f"sqlite:///{DEFAULT_DB_PATH}"
    # Cors for local static frontend served by FastAPI or a separate port
    cors_origins: str = "*"

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
