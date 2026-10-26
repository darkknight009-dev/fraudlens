from collections.abc import Iterator

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.main import app
from app.models.api_key import APIKey, APIKeyScope
from app.models.rule_set import RuleSetVersion
from app.models.tenant import Tenant
from app.services.auth import generate_api_key
from app.services.rules import DEFAULT_RULE_CONFIGURATION


def config_settings() -> Settings:
    return Settings(app_env="test", api_key_hash_pepper="test-pepper-with-at-least-32-characters")


def test_rule_configuration_is_tenant_scoped_and_versioned(db_session: Session) -> None:
    tenant = Tenant(name="Config Tenant")
    db_session.add(tenant)
    db_session.commit()
    generated = generate_api_key(config_settings().api_key_hash_pepper)
    db_session.add(
        APIKey(
            tenant_id=tenant.id,
            key_prefix=generated.prefix,
            key_hash=generated.digest,
            created_by="test",
            scopes=[APIKeyScope(scope="config:read"), APIKeyScope(scope="config:write")],
        )
    )
    db_session.commit()

    def override_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = config_settings
    try:
        client = TestClient(app)
        headers = {"Authorization": f"Bearer {generated.plaintext}"}
        initial = client.get("/v1/config/rules", headers=headers)
        assert initial.status_code == 200
        assert initial.json()["version"] == "rules-v1"
        configuration = {**DEFAULT_RULE_CONFIGURATION, "version": "rules-v2"}
        replaced = client.put(
            "/v1/config/rules",
            json={"configuration": configuration},
            headers=headers,
        )
        assert replaced.status_code == 200
        assert replaced.json()["version"] == "rules-v2"
        versions = db_session.scalars(
            select(RuleSetVersion).where(RuleSetVersion.tenant_id == tenant.id)
        ).all()
        assert len(versions) == 1
        assert versions[0].is_active is True
    finally:
        app.dependency_overrides.clear()
