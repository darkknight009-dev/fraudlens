"""Dispatch due webhook deliveries once; schedule this from a bounded worker."""

from datetime import UTC, datetime

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import get_session_factory
from app.models.webhook import WebhookDelivery, WebhookEndpoint
from app.services.webhooks import dispatch_delivery


def main() -> None:
    settings = get_settings()
    with get_session_factory(settings.database_url)() as session:
        now = datetime.now(UTC)
        deliveries = session.scalars(
            select(WebhookDelivery)
            .where(
                WebhookDelivery.status.in_(["pending", "retrying"]),
                (WebhookDelivery.next_attempt_at.is_(None))
                | (WebhookDelivery.next_attempt_at <= now),
            )
            .order_by(WebhookDelivery.created_at)
            .limit(100)
        ).all()
        for delivery in deliveries:
            endpoint = session.get(WebhookEndpoint, delivery.endpoint_id)
            if endpoint is not None and endpoint.is_active:
                dispatch_delivery(session, delivery, endpoint, settings)
        print(f"Processed {len(deliveries)} webhook deliveries.")


if __name__ == "__main__":
    main()
