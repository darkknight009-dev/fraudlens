"""Sandbox payment lifecycle schemas."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.transactions import Channel


class TestPaymentMethod(StrEnum):
    APPROVED = "test_approved"
    DECLINED = "test_declined"
    TIMEOUT = "test_timeout"


class PaymentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    merchant_order_id: str = Field(min_length=1, max_length=128)
    amount_minor: int = Field(gt=0, le=9_223_372_036_854_775_807)
    currency: str = Field(min_length=3, max_length=3)
    account_ref: str = Field(min_length=1, max_length=128)
    device_ref: str | None = Field(default=None, max_length=128)
    merchant_ref: str | None = Field(default=None, max_length=128)
    channel: Channel
    payment_method: TestPaymentMethod
    metadata: dict[str, str | int | bool] = Field(default_factory=dict, max_length=10)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        normalized = value.upper()
        if not normalized.isalpha() or len(normalized) != 3:
            raise ValueError("must be a three-letter ISO currency code")
        return normalized


class PaymentAttemptResponse(BaseModel):
    id: str
    provider: str
    status: str
    provider_reference: str | None
    response_metadata: dict[str, str | int | bool]
    created_at: datetime


class PaymentTimelineStep(BaseModel):
    name: str
    status: str
    detail: str


class PaymentResponse(BaseModel):
    id: str
    merchant_order_id: str
    amount_minor: int
    currency: str
    channel: str
    payment_method_label: str
    payment_status: str
    provider_status: str
    provider_reference: str | None
    risk_score: int | None
    risk_level: str | None
    risk_recommendation: str | None
    assessment_id: str | None
    transaction_id: str | None
    merchant_decision: str | None
    created_at: datetime
    updated_at: datetime
    attempts: list[PaymentAttemptResponse]
    timeline: list[PaymentTimelineStep]
    metadata: dict[str, Any]


class PaymentList(BaseModel):
    items: list[PaymentResponse]
    limit: int
    offset: int
    total: int
