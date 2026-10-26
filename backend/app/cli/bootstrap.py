"""Create a development tenant and integration key."""

import argparse

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_session_factory
from app.models.api_key import APIKey, APIKeyScope
from app.models.audit_event import AuditEvent
from app.models.tenant import Tenant
from app.services.auth import generate_api_key, validate_scopes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default="FraudLens Demo Tenant")
    parser.add_argument("--created-by", default="local-bootstrap")
    parser.add_argument("--scope", action="append", dest="scopes")
    return parser.parse_args()


def bootstrap(session: Session, name: str, created_by: str, scopes: list[str] | None) -> str:
    settings = get_settings()
    if settings.app_env not in {"development", "test"}:
        raise RuntimeError(
            "The bootstrap command is disabled outside development and test environments."
        )
    selected_scopes = validate_scopes(scopes or ["transactions:score"])
    generated = generate_api_key(settings.api_key_hash_pepper)
    tenant = Tenant(name=name)
    session.add(tenant)
    session.flush()
    api_key = APIKey(
        tenant_id=tenant.id,
        key_prefix=generated.prefix,
        key_hash=generated.digest,
        created_by=created_by,
    )
    api_key.scopes = [APIKeyScope(scope=scope) for scope in sorted(selected_scopes)]
    session.add(api_key)
    session.add(
        AuditEvent(
            tenant_id=tenant.id,
            actor_type="bootstrap",
            actor_id=created_by,
            action="api_key.created",
            target_type="api_key",
            target_id=str(api_key.id),
            details_redacted={"key_prefix": generated.prefix, "scopes": sorted(selected_scopes)},
        )
    )
    session.commit()
    return generated.plaintext


def main() -> None:
    args = parse_args()
    settings = get_settings()
    factory = get_session_factory(settings.database_url)
    with factory() as session:
        plaintext = bootstrap(session, args.name, args.created_by, args.scopes)
    print("Tenant and API key created. Store this key securely; it will not be shown again:")
    print(plaintext)


if __name__ == "__main__":
    main()
