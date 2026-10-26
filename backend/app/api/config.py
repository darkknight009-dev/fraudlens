"""Tenant-scoped rule configuration management."""

from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.session import get_db
from app.models.rule_set import RuleSetVersion
from app.schemas.rules import RuleConfigurationResponse, RuleConfigurationUpdate
from app.services.audit import record_audit
from app.services.auth import Principal, require_scope
from app.services.rules import DEFAULT_RULE_CONFIGURATION, RuleConfiguration

router = APIRouter(prefix="/v1/config/rules", tags=["configuration"])


def _active(session: Session, tenant_id: UUID) -> RuleSetVersion | None:
    return session.scalar(
        select(RuleSetVersion)
        .where(RuleSetVersion.tenant_id == tenant_id, RuleSetVersion.is_active.is_(True))
        .order_by(RuleSetVersion.created_at.desc())
    )


@router.get("", response_model=RuleConfigurationResponse)
def get_rules(
    principal: Principal = Depends(require_scope("config:read")),  # noqa: B008
    session: Session = Depends(get_db),  # noqa: B008
) -> RuleConfigurationResponse:
    rule_set = _active(session, principal.tenant_id)
    if rule_set is None:
        configuration = RuleConfiguration.model_validate(DEFAULT_RULE_CONFIGURATION)
        return RuleConfigurationResponse(
            version=configuration.version, configuration=configuration.model_dump()
        )
    return RuleConfigurationResponse(version=rule_set.version, configuration=rule_set.configuration)


@router.put("", response_model=RuleConfigurationResponse)
def replace_rules(
    update: RuleConfigurationUpdate,
    request: Request,
    principal: Principal = Depends(require_scope("config:write")),  # noqa: B008
    session: Session = Depends(get_db),  # noqa: B008
) -> RuleConfigurationResponse:
    configuration = RuleConfiguration.model_validate(update.configuration)
    current = _active(session, principal.tenant_id)
    if current is not None:
        current.is_active = False
    duplicate = session.scalar(
        select(RuleSetVersion).where(
            RuleSetVersion.tenant_id == principal.tenant_id,
            RuleSetVersion.version == configuration.version,
        )
    )
    if duplicate is not None:
        raise AppError("RULE_VERSION_EXISTS", "Rule-set version already exists.", 409)
    rule_set = RuleSetVersion(
        tenant_id=principal.tenant_id,
        version=configuration.version,
        configuration=configuration.model_dump(),
        created_by=str(principal.api_key_id),
        is_active=True,
    )
    session.add(rule_set)
    record_audit(
        session,
        tenant_id=principal.tenant_id,
        actor_type="api_key",
        actor_id=str(principal.api_key_id),
        action="rule_set.activated",
        target_type="rule_set_version",
        target_id=configuration.version,
        request_id=request.state.request_id,
        details={"version": configuration.version},
    )
    session.commit()
    return RuleConfigurationResponse(
        version=configuration.version, configuration=configuration.model_dump()
    )
