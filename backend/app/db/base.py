"""SQLAlchemy declarative base and model registration."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def import_models() -> None:
    """Register all models before metadata inspection or migration generation."""

    from app.models import (  # noqa: F401
        alert,
        api_key,
        assessment,
        audit_event,
        event,
        idempotency,
        payment,
        rule_set,
        tenant,
        transaction,
        webhook,
    )
