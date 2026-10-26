"""Integration API-key persistence models."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class APIKey(Base):
    __tablename__ = "api_keys"
    __table_args__ = (Index("ix_api_keys_prefix", "key_prefix"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    key_prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    tenant: Mapped["Tenant"] = relationship(back_populates="api_keys")
    scopes: Mapped[list["APIKeyScope"]] = relationship(
        back_populates="api_key", cascade="all, delete-orphan", lazy="selectin"
    )


class APIKeyScope(Base):
    __tablename__ = "api_key_scopes"

    api_key_id: Mapped[UUID] = mapped_column(
        ForeignKey("api_keys.id", ondelete="CASCADE"), primary_key=True
    )
    scope: Mapped[str] = mapped_column(String(100), primary_key=True)

    api_key: Mapped[APIKey] = relationship(back_populates="scopes")


from app.models.tenant import Tenant  # noqa: E402, F401
