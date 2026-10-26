"""Risk scoring request and response schemas."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.transactions import CanonicalTransaction


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AssessmentStatus(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"


class SignalSource(StrEnum):
    RULE = "rule"
    MODEL = "model"
    FEATURE = "feature"


class SignalSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskSignalResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    reason_code: str
    message: str
    source: SignalSource
    severity: SignalSeverity
    evidence: dict[str, Any]
    contribution: int


class DetectorStatus(BaseModel):
    rules: str = "complete"
    ml: str = "disabled"


class ScoreResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    assessment_id: str
    transaction_id: str
    risk_score: int = Field(ge=0, le=100)
    risk_level: RiskLevel
    mode: str
    assessment_status: AssessmentStatus
    signals: list[RiskSignalResponse]
    detector_status: DetectorStatus
    rule_set_version: str
    model_version: str | None
    request_id: str


class AssessmentList(BaseModel):
    items: list[ScoreResponse]
    limit: int
    offset: int
    total: int


ScoreRequest = CanonicalTransaction
