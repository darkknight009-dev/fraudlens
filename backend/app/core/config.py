"""Environment-driven application settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated configuration for the API process."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: Literal["development", "test", "staging", "production"] = "development"
    log_level: str = "INFO"
    database_url: str = "postgresql+psycopg://fraudlens:fraudlens_dev@localhost:5432/fraudlens"
    api_key_hash_pepper: str = "development-only-change-me"
    cors_allowed_origins: str = "http://localhost:5173"
    rate_limit_requests_per_minute: int = Field(default=120, ge=1, le=100_000)
    max_request_body_bytes: int = Field(default=65_536, ge=1_024, le=10_485_760)
    idempotency_ttl_seconds: int = Field(default=86_400, ge=60, le=2_592_000)
    risk_mode_default: Literal["shadow", "advisory"] = "shadow"
    model_artifact_path: str | None = None
    retention_transaction_days: int = Field(default=30, ge=1)
    retention_audit_days: int = Field(default=365, ge=1)
    webhook_encryption_key: str | None = None
    webhook_timeout_seconds: float = Field(default=2.0, gt=0, le=30)
    webhook_max_attempts: int = Field(default=5, ge=1, le=20)

    @property
    def cors_origins(self) -> tuple[str, ...]:
        return tuple(
            origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()
        )

    @model_validator(mode="after")
    def validate_runtime_security(self) -> "Settings":
        if self.app_env == "production":
            if self.api_key_hash_pepper == "development-only-change-me":
                raise ValueError("API_KEY_HASH_PEPPER must be replaced in production")
            if len(self.api_key_hash_pepper) < 32:
                raise ValueError("API_KEY_HASH_PEPPER must contain at least 32 characters")
            if self.database_url.startswith("sqlite"):
                raise ValueError("PostgreSQL is required in production")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
