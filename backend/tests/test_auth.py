from datetime import UTC, datetime, timedelta

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import AppError, app_error_handler
from app.models.api_key import APIKey, APIKeyScope
from app.models.tenant import Tenant
from app.repositories.api_keys import list_api_keys_for_tenant
from app.services.auth import (
    Principal,
    authenticate_api_key,
    generate_api_key,
    require_scope,
)


def settings() -> Settings:
    return Settings(app_env="test", api_key_hash_pepper="test-pepper-with-at-least-32-characters")


def add_key(
    db_session: Session,
    tenant: Tenant,
    scopes: list[str],
    expires_at: datetime | None = None,
    revoked_at: datetime | None = None,
) -> str:
    generated = generate_api_key(settings().api_key_hash_pepper)
    key = APIKey(
        tenant_id=tenant.id,
        key_prefix=generated.prefix,
        key_hash=generated.digest,
        created_by="test",
        expires_at=expires_at,
        revoked_at=revoked_at,
        scopes=[APIKeyScope(scope=scope) for scope in scopes],
    )
    db_session.add(key)
    db_session.commit()
    return generated.plaintext


def test_valid_key_resolves_only_its_tenant(db_session: Session) -> None:
    tenant_a = Tenant(name="Tenant A")
    tenant_b = Tenant(name="Tenant B")
    db_session.add_all([tenant_a, tenant_b])
    db_session.commit()
    key_a = add_key(db_session, tenant_a, ["transactions:score"])
    add_key(db_session, tenant_b, ["transactions:read"])

    principal = authenticate_api_key(db_session, key_a, settings())

    assert principal.tenant_id == tenant_a.id
    assert principal.scopes == {"transactions:score"}
    assert [key.tenant_id for key in list_api_keys_for_tenant(db_session, tenant_a.id)] == [
        tenant_a.id
    ]


def test_invalid_expired_and_revoked_keys_are_rejected(db_session: Session) -> None:
    tenant = Tenant(name="Tenant")
    db_session.add(tenant)
    db_session.commit()
    expired = add_key(
        db_session, tenant, ["transactions:score"], datetime.now(UTC) - timedelta(minutes=1)
    )
    revoked = add_key(db_session, tenant, ["transactions:score"], revoked_at=datetime.now(UTC))

    for plaintext in ["fl_invalid", expired, revoked]:
        try:
            authenticate_api_key(db_session, plaintext, settings())
        except Exception as exc:
            assert exc.__class__.__name__ == "AuthenticationError"
        else:
            raise AssertionError("invalid credential was accepted")


def test_protected_request_enforces_authentication_and_scope(db_session: Session) -> None:
    tenant = Tenant(name="Tenant")
    db_session.add(tenant)
    db_session.commit()
    read_key = add_key(db_session, tenant, ["transactions:read"])

    test_app = FastAPI()
    test_app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]

    @test_app.get("/protected")
    def protected(
        principal: Principal = Depends(require_scope("transactions:score")),  # noqa: B008
    ) -> dict[str, str]:
        return {"tenant_id": str(principal.tenant_id)}

    from app.db.session import get_db

    test_app.dependency_overrides[get_db] = lambda: db_session
    test_app.dependency_overrides[get_settings] = settings
    client = TestClient(test_app)

    assert client.get("/protected").status_code == 401
    response = client.get("/protected", headers={"Authorization": f"Bearer {read_key}"})
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "INSUFFICIENT_SCOPE"


def test_api_key_hash_is_not_plaintext(db_session: Session) -> None:
    tenant = Tenant(name="Tenant")
    db_session.add(tenant)
    db_session.commit()
    plaintext = add_key(db_session, tenant, ["transactions:score"])

    stored_hash = db_session.scalar(select(APIKey.key_hash))

    assert stored_hash != plaintext
    assert len(stored_hash or "") == 64
