"""Synthetic payment checkout and mock-provider persistence."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.types import JSON_TYPE


class PaymentIntent(Base):
    """Merchant-side payment record; never stores payment credentials."""

    __tablename__ = "payment_intents"
    __table_args__ = (
        Index("ix_payment_intents_tenant_created", "tenant_id", "created_at"),
        UniqueConstraint("tenant_id", "merchant_order_id", name="uq_payment_intents_tenant_order"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    merchant_order_id: Mapped[str] = mapped_column(String(128), nullable=False)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    payment_method_label: Mapped[str] = mapped_column(String(64), nullable=False)
    payment_status: Mapped[str] = mapped_column(String(24), nullable=False, default="processing")
    provider_status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    provider_reference: Mapped[str | None] = mapped_column(String(128))
    risk_score: Mapped[int | None] = mapped_column(Integer)
    risk_level: Mapped[str | None] = mapped_column(String(16))
    risk_recommendation: Mapped[str | None] = mapped_column(String(24))
    assessment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("assessments.id", ondelete="SET NULL")
    )
    transaction_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("transactions.id", ondelete="SET NULL")
    )
    merchant_decision: Mapped[str | None] = mapped_column(String(32))
    safe_metadata: Mapped[dict[str, str | int | bool]] = mapped_column(
        JSON_TYPE, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class PaymentAttempt(Base):
    """Safe provider-attempt record containing synthetic gateway data only."""

    __tablename__ = "payment_attempts"
    __table_args__ = (Index("ix_payment_attempts_tenant_created", "tenant_id", "created_at"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    payment_intent_id: Mapped[UUID] = mapped_column(
        ForeignKey("payment_intents.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(
        String(32), nullable=False, default="fraudlens_mock_gateway"
    )
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    provider_reference: Mapped[str | None] = mapped_column(String(128))
    response_metadata: Mapped[dict[str, str | int | bool]] = mapped_column(
        JSON_TYPE, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
