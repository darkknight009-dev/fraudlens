"""Process a bounded batch of durable asynchronous transaction events."""

from datetime import UTC, datetime

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import get_session_factory
from app.models.event import EventInbox
from app.schemas.transactions import CanonicalTransaction
from app.services.auth import Principal
from app.services.scoring import score_transaction


def main() -> None:
    settings = get_settings()
    processed = 0
    with get_session_factory(settings.database_url)() as session:
        events = session.scalars(
            select(EventInbox)
            .where(EventInbox.status == "pending")
            .order_by(EventInbox.created_at)
            .limit(100)
        ).all()
        for event in events:
            event.attempt_count += 1
            principal = Principal(
                event.tenant_id, event.api_key_id, frozenset({"transactions:score"})
            )
            try:
                score_transaction(
                    session,
                    principal,
                    CanonicalTransaction.model_validate(event.payload),
                    request_id=f"event_{event.event_id}",
                    idempotency_key=f"event:{event.event_id}",
                    settings=settings,
                )
                event.status = "processed"
                event.processed_at = datetime.now(UTC)
                session.commit()
                processed += 1
            except Exception:
                session.rollback()
                failed_event = session.get(EventInbox, event.id)
                if failed_event is not None:
                    failed_event.status = "failed" if failed_event.attempt_count >= 5 else "pending"
                    failed_event.last_error = "event processing failed"
                    session.commit()
    print(f"Processed {processed} asynchronous events.")


if __name__ == "__main__":
    main()
