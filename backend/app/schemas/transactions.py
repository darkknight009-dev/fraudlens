"""Canonical transaction request schema."""

import re
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

REFERENCE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
METADATA_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,31}$")
ALLOWED_METADATA_KEYS = frozenset({"source", "integration_version", "provider_event_type"})
FORBIDDEN_FIELD_NAMES = frozenset(
    {
        "pan",
        "card_number",
        "cvv",
        "pin",
        "otp",
        "password",
        "secret",
        "token",
        "bank_login",
    }
)


class Channel(StrEnum):
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    WALLET = "wallet"
    UPI = "upi"
    OTHER = "other"


class CanonicalTransaction(BaseModel):
    """Validated, provider-neutral transaction data."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    transaction_id: str = Field(min_length=1, max_length=128)
    amount_minor: int = Field(ge=0, le=9_223_372_036_854_775_807)
    currency: str = Field(min_length=3, max_length=3)
    occurred_at: datetime
    account_ref: str = Field(min_length=1, max_length=128)
    device_ref: str | None = Field(default=None, max_length=128)
    merchant_ref: str | None = Field(default=None, max_length=128)
    channel: Channel
    provider_status: str | None = Field(default=None, max_length=32)
    metadata: dict[str, str | int | bool] = Field(default_factory=dict, max_length=10)

    @field_validator("transaction_id", "account_ref", "device_ref", "merchant_ref")
    @classmethod
    def validate_reference(cls, value: str | None) -> str | None:
        if value is not None and not REFERENCE_PATTERN.fullmatch(value):
            raise ValueError("must contain only safe pseudonymous reference characters")
        return value

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        normalized = value.upper()
        if not re.fullmatch(r"[A-Z]{3}", normalized):
            raise ValueError("must be a three-letter ISO currency code")
        return normalized

    @field_validator("occurred_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("must include a timezone offset")
        return value.astimezone(UTC)

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, str | int | bool]) -> dict[str, str | int | bool]:
        unknown = set(value) - ALLOWED_METADATA_KEYS
        invalid_keys = [key for key in value if not METADATA_KEY_PATTERN.fullmatch(key)]
        forbidden = set(value) & FORBIDDEN_FIELD_NAMES
        if unknown or invalid_keys or forbidden:
            raise ValueError("metadata contains a field that is not allowlisted")
        for key, item in value.items():
            if isinstance(item, str) and len(item) > 128:
                raise ValueError(f"metadata.{key} is too long")
        return value

    @model_validator(mode="after")
    def reject_sensitive_values(self) -> "CanonicalTransaction":
        values: list[Any] = [
            self.transaction_id,
            self.account_ref,
            self.device_ref,
            self.merchant_ref,
            *self.metadata.keys(),
        ]
        lowered = " ".join(str(value).lower() for value in values)
        if any(term in lowered for term in FORBIDDEN_FIELD_NAMES):
            raise ValueError("sensitive payment credentials are not accepted")
        return self
