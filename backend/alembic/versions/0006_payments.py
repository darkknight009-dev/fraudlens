"""Create sandbox payment intent and attempt tables.

Revision ID: 0006_payments
Revises: 0005_event_inbox
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0006_payments"
down_revision: str | None = "0005_event_inbox"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "payment_intents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("merchant_order_id", sa.String(length=128), nullable=False),
        sa.Column("amount_minor", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("payment_method_label", sa.String(length=64), nullable=False),
        sa.Column("payment_status", sa.String(length=24), nullable=False),
        sa.Column("provider_status", sa.String(length=24), nullable=False),
        sa.Column("provider_reference", sa.String(length=128), nullable=True),
        sa.Column("risk_score", sa.Integer(), nullable=True),
        sa.Column("risk_level", sa.String(length=16), nullable=True),
        sa.Column("risk_recommendation", sa.String(length=24), nullable=True),
        sa.Column("assessment_id", sa.Uuid(), nullable=True),
        sa.Column("transaction_id", sa.Uuid(), nullable=True),
        sa.Column("merchant_decision", sa.String(length=32), nullable=True),
        sa.Column("safe_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id", "merchant_order_id", name="uq_payment_intents_tenant_order"
        ),
    )
    op.create_index(
        "ix_payment_intents_tenant_created", "payment_intents", ["tenant_id", "created_at"]
    )
    op.create_table(
        "payment_attempts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("payment_intent_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("provider_reference", sa.String(length=128), nullable=True),
        sa.Column("response_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["payment_intent_id"], ["payment_intents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_payment_attempts_tenant_created", "payment_attempts", ["tenant_id", "created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_payment_attempts_tenant_created", table_name="payment_attempts")
    op.drop_table("payment_attempts")
    op.drop_index("ix_payment_intents_tenant_created", table_name="payment_intents")
    op.drop_table("payment_intents")
