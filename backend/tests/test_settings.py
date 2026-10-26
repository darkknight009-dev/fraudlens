import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_cors_origins_are_parsed_from_environment_style_value() -> None:
    settings = Settings(cors_allowed_origins="http://localhost:5173, https://demo.example")

    assert settings.cors_origins == ("http://localhost:5173", "https://demo.example")


def test_production_rejects_development_secret() -> None:
    with pytest.raises(ValidationError):
        Settings(app_env="production", api_key_hash_pepper="development-only-change-me")


def test_production_requires_long_secret() -> None:
    with pytest.raises(ValidationError):
        Settings(app_env="production", api_key_hash_pepper="too-short")
