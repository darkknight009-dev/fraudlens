"""API-key generation, verification, and authorization services."""

import hashlib
import hmac
import secrets
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppError, AuthenticationError, AuthorizationError
from app.models.api_key import APIKey

Scope = Literal[
    "transactions:score",
    "transactions:read",
    "cases:read",
    "cases:write",
    "config:read",
    "config:write",
    "audit:read",
]
ALL_SCOPES: frozenset[str] = frozenset(
    {
        "transactions:score",
        "transactions:read",
        "cases:read",
        "cases:write",
        "config:read",
        "config:write",
        "audit:read",
    }
)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


@dataclass(frozen=True)
class GeneratedAPIKey:
    plaintext: str
    prefix: str
    digest: str


@dataclass(frozen=True)
class Principal:
    tenant_id: UUID
    api_key_id: UUID
    scopes: frozenset[str]


def hash_api_key(plaintext: str, pepper: str) -> str:
    return hmac.new(pepper.encode("utf-8"), plaintext.encode("utf-8"), hashlib.sha256).hexdigest()


def generate_api_key(pepper: str) -> GeneratedAPIKey:
    plaintext = f"fl_{secrets.token_urlsafe(32)}"
    return GeneratedAPIKey(plaintext, plaintext[:16], hash_api_key(plaintext, pepper))


def validate_scopes(scopes: Iterable[str]) -> frozenset[str]:
    normalized = frozenset(scopes)
    unknown = normalized - ALL_SCOPES
    if unknown:
        raise AppError(
            "INVALID_SCOPE",
            "One or more API-key scopes are invalid.",
            422,
            [{"scope": scope} for scope in sorted(unknown)],
        )
    if not normalized:
        raise AppError("INVALID_SCOPE", "At least one API-key scope is required.", 422)
    return normalized


def authenticate_api_key(session: Session, plaintext: str | None, settings: Settings) -> Principal:
    if not plaintext or not plaintext.startswith("fl_"):
        raise AuthenticationError()

    prefix = plaintext[:16]
    candidates = session.scalars(
        select(APIKey).where(APIKey.key_prefix == prefix, APIKey.revoked_at.is_(None))
    ).all()
    now = datetime.now(UTC)
    expected = hash_api_key(plaintext, settings.api_key_hash_pepper)
    for api_key in candidates:
        if api_key.expires_at is not None and _as_utc(api_key.expires_at) <= now:
            continue
        if secrets.compare_digest(api_key.key_hash, expected):
            api_key.last_used_at = now
            session.commit()
            return Principal(
                tenant_id=api_key.tenant_id,
                api_key_id=api_key.id,
                scopes=frozenset(scope.scope for scope in api_key.scopes),
            )
    raise AuthenticationError()


def require_scope(scope: Scope) -> Callable[..., Principal]:
    """Build a FastAPI dependency for one documented scope."""

    from fastapi import Depends, Header

    from app.core.config import get_settings
    from app.db.session import get_db

    def dependency(
        authorization: str | None = Header(default=None),
        session: Session = Depends(get_db),  # noqa: B008
        settings: Settings = Depends(get_settings),  # noqa: B008
    ) -> Principal:
        scheme, _, credentials = (authorization or "").partition(" ")
        plaintext = credentials if scheme.lower() == "bearer" else None
        principal = authenticate_api_key(session, plaintext, settings)
        if scope not in principal.scopes:
            raise AuthorizationError(scope)
        return principal

    return dependency
