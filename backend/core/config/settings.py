from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.core.constants.enums import Environment, LLMMode


class Settings(BaseSettings):
    """Application-wide settings loaded from environment variables / .env file.

    Field names map to env vars case-insensitively (e.g. ``database_url`` ↔ ``DATABASE_URL``).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    env: Environment = Environment.DEVELOPMENT
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    database_url: str = "postgresql://user:password@localhost:5432/ai_org_simulation"

    gcp_project_id: str | None = None
    google_application_credentials: str | None = None
    vertex_location: str = "asia-northeast3"
    vertex_model: str = "gemini-2.5-pro"
    firestore_emulator_host: str | None = None

    llm_mode: LLMMode = LLMMode.STUB

    cors_allow_origins: list[str] = ["*"]


@lru_cache
def get_settings() -> Settings:
    """Cached accessor so the .env file is parsed only once per process."""
    return Settings()
