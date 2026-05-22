import json
from functools import lru_cache
from typing import Literal

from pydantic import Field
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

    # SQLAlchemy URL — psycopg(3) 드라이버를 명시한다.
    # 일반 ``postgresql://``로 시작하면 SQLAlchemy가 psycopg2를 우선 찾아서 실패한다.
    database_url: str = "postgresql+psycopg://user:password@localhost:5432/ai_org_simulation"
    db_echo: bool = False

    gcp_project_id: str | None = None
    google_application_credentials: str | None = None
    vertex_location: str = "asia-northeast3"
    vertex_model: str = "gemini-2.5-pro"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-pro"
    firestore_emulator_host: str | None = None

    llm_mode: LLMMode = LLMMode.STUB

    cors_allow_origins_raw: str = Field(default='["*"]', alias="CORS_ALLOW_ORIGINS")

    @property
    def cors_allow_origins(self) -> list[str]:
        """CORS origins normalized from JSON, comma-separated, or shell-stripped values."""

        value = self.cors_allow_origins_raw.strip()
        if not value:
            return ["*"]

        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            parsed = None

        if isinstance(parsed, list):
            return [str(origin).strip() for origin in parsed if str(origin).strip()]
        if isinstance(parsed, str):
            return [parsed]

        if value == "[*]":
            return ["*"]
        if value.startswith("[") and value.endswith("]"):
            value = value[1:-1]
        return [origin.strip().strip("\"'") for origin in value.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached accessor so the .env file is parsed only once per process."""
    return Settings()
