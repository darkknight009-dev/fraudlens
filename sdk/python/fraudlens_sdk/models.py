"""SDK models aligned to the public `/v1` contract."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Transaction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transaction_id: str = Field(min_length=1, max_length=128)
    amount_minor: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    occurred_at: datetime
    account_ref: str = Field(min_length=1, max_length=128)
    device_ref: str | None = None
    merchant_ref: str | None = None
    channel: str
    provider_status: str | None = None
    metadata: dict[str, str | int | bool] = Field(default_factory=dict)


class RiskSignal(BaseModel):
    reason_code: str
    message: str
    source: str
    severity: str
    evidence: dict[str, Any]
    contribution: int


class RiskAssessment(BaseModel):
    assessment_id: str
    transaction_id: str
    risk_score: int = Field(ge=0, le=100)
    risk_level: str
    mode: str
    assessment_status: str
    signals: list[RiskSignal]
    detector_status: dict[str, str]
    rule_set_version: str
    model_version: str | None
    request_id: str
