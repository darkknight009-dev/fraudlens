"""Create canonical transaction and scoring tables.

Revision ID: 0002_scoring
Revises: 0001_foundation
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002_scoring"
down_revision: str | None = "0001_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("external_transaction_id", sa.String(length=128), nullable=False),
        sa.Column("amount_minor", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("account_ref_hash", sa.String(length=64), nullable=False),
        sa.Column("device_ref_hash", sa.String(length=64), nullable=True),
        sa.Column("merchant_ref", sa.String(length=128), nullable=True),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("provider_status", sa.String(length=32), nullable=True),
        sa.Column("safe_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id", "external_transaction_id", name="uq_transactions_tenant_external"
        ),
    )
    op.create_index("ix_transactions_tenant_created", "transactions", ["tenant_id", "created_at"])

    op.create_table(
        "rule_set_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("configuration", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_by", sa.String(length=200), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rule_sets_tenant_active", "rule_set_versions", ["tenant_id", "is_active"])

    op.create_table(
        "assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("transaction_id", sa.Uuid(), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("risk_level", sa.String(length=16), nullable=False),
        sa.Column("mode", sa.String(length=16), nullable=False),
        sa.Column("assessment_status", sa.String(length=16), nullable=False),
        sa.Column("rule_set_version", sa.String(length=64), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=True),
        sa.Column("feature_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("detector_status", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("request_id", sa.String(length=128), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "risk_score >= 0 AND risk_score <= 100", name="ck_assessments_risk_score"
        ),
        sa.CheckConstraint("mode IN ('shadow', 'advisory')", name="ck_assessments_mode"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_assessments_tenant_created", "assessments", ["tenant_id", "created_at"])

    op.create_table(
        "risk_signals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("assessment_id", sa.Uuid(), nullable=False),
        sa.Column("reason_code", sa.String(length=64), nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("message_template_key", sa.String(length=128), nullable=False),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("contribution", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_risk_signals_tenant_assessment", "risk_signals", ["tenant_id", "assessment_id"]
    )

    op.create_table(
        "idempotency_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("endpoint", sa.String(length=128), nullable=False),
        sa.Column("key_hash", sa.String(length=64), nullable=False),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=False),
        sa.Column("response_body", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_idempotency_tenant_endpoint_key",
        "idempotency_records",
        ["tenant_id", "endpoint", "key_hash"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_idempotency_tenant_endpoint_key", table_name="idempotency_records")
    op.drop_table("idempotency_records")
    op.drop_index("ix_risk_signals_tenant_assessment", table_name="risk_signals")
    op.drop_table("risk_signals")
    op.drop_index("ix_assessments_tenant_created", table_name="assessments")
    op.drop_table("assessments")
    op.drop_index("ix_rule_sets_tenant_active", table_name="rule_set_versions")
    op.drop_table("rule_set_versions")
    op.drop_index("ix_transactions_tenant_created", table_name="transactions")
    op.drop_table("transactions")
