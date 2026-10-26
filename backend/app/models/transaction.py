"""Canonical transaction persistence model."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.types import JSON_TYPE


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "external_transaction_id", name="uq_transactions_tenant_external"
        ),
        Index("ix_transactions_tenant_created", "tenant_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    external_transaction_id: Mapped[str] = mapped_column(String(128), nullable=False)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    account_ref_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    device_ref_hash: Mapped[str | None] = mapped_column(String(64))
    merchant_ref: Mapped[str | None] = mapped_column(String(128))
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_status: Mapped[str | None] = mapped_column(String(32))
    safe_metadata: Mapped[dict[str, str | int | bool]] = mapped_column(
        JSON_TYPE, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
