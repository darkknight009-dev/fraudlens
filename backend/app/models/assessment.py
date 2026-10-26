"""Risk assessment and explainable signal persistence models."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.types import JSON_TYPE


class Assessment(Base):
    __tablename__ = "assessments"
    __table_args__ = (Index("ix_assessments_tenant_created", "tenant_id", "created_at"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    transaction_id: Mapped[UUID] = mapped_column(
        ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False
    )
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False)
    mode: Mapped[str] = mapped_column(String(16), nullable=False)
    assessment_status: Mapped[str] = mapped_column(String(16), nullable=False)
    rule_set_version: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[str | None] = mapped_column(String(64))
    feature_snapshot: Mapped[dict[str, object]] = mapped_column(
        JSON_TYPE, nullable=False, default=dict
    )
    detector_status: Mapped[dict[str, str]] = mapped_column(JSON_TYPE, nullable=False, default=dict)
    request_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class RiskSignal(Base):
    __tablename__ = "risk_signals"
    __table_args__ = (Index("ix_risk_signals_tenant_assessment", "tenant_id", "assessment_id"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    assessment_id: Mapped[UUID] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False
    )
    reason_code: Mapped[str] = mapped_column(String(64), nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    message_template_key: Mapped[str] = mapped_column(String(128), nullable=False)
    evidence: Mapped[dict[str, object]] = mapped_column(JSON_TYPE, nullable=False, default=dict)
    contribution: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
