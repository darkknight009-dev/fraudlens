"""Create alert and case-note tables.

Revision ID: 0003_alerts
Revises: 0002_scoring
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_alerts"
down_revision: str | None = "0002_scoring"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "alerts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("assessment_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="open", nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("assigned_to", sa.String(length=200), nullable=True),
        sa.Column("disposition", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('open', 'in_review', 'resolved', 'false_positive', 'escalated')",
            name="ck_alerts_status",
        ),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "assessment_id", name="uq_alerts_tenant_assessment"),
    )
    op.create_index(
        "ix_alerts_tenant_status_created", "alerts", ["tenant_id", "status", "created_at"]
    )
    op.create_table(
        "case_notes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.String(length=200), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["case_id"], ["alerts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_case_notes_tenant_case_created",
        "case_notes",
        ["tenant_id", "case_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_case_notes_tenant_case_created", table_name="case_notes")
    op.drop_table("case_notes")
    op.drop_index("ix_alerts_tenant_status_created", table_name="alerts")
    op.drop_table("alerts")
