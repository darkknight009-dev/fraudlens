"""API-key repository methods with explicit tenant scope."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.api_key import APIKey


def list_api_keys_for_tenant(session: Session, tenant_id: UUID) -> list[APIKey]:
    """Return only keys belonging to the authenticated tenant."""

    return list(session.scalars(select(APIKey).where(APIKey.tenant_id == tenant_id)).all())
