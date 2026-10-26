"""Synthetic checkout and payment lifecycle endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.schemas.payments import PaymentCreate, PaymentList, PaymentResponse
from app.services.auth import Principal, require_scope
from app.services.payments import create_payment, get_payment, list_payments

router = APIRouter(prefix="/v1/sandbox/payments", tags=["sandbox-payments"])


@router.post("", response_model=PaymentResponse, status_code=201)
def create_sandbox_payment(
    payment: PaymentCreate,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    principal: Principal = Depends(require_scope("transactions:score")),  # noqa: B008
    session: Session = Depends(get_db),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> PaymentResponse:
    return create_payment(
        session,
        principal,
        payment,
        idempotency_key=idempotency_key,
        request_id=request.state.request_id,
        settings=settings,
    )


@router.get("", response_model=PaymentList)
def list_sandbox_payments(
    principal: Principal = Depends(require_scope("transactions:read")),  # noqa: B008
    session: Session = Depends(get_db),  # noqa: B008
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> PaymentList:
    return list_payments(session, principal.tenant_id, limit, offset)


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_sandbox_payment(
    payment_id: UUID,
    principal: Principal = Depends(require_scope("transactions:read")),  # noqa: B008
    session: Session = Depends(get_db),  # noqa: B008
) -> PaymentResponse:
    return get_payment(session, principal.tenant_id, payment_id)
