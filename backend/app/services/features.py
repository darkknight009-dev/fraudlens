"""Point-in-time feature extraction for synthetic and future model inputs."""

from datetime import datetime
from typing import TypedDict


class SyntheticRecord(TypedDict):
    transaction_id: str
    amount_minor: int
    occurred_at: str
    account_velocity_5m: int
    device_velocity_5m: int
    channel_code: int
    scenario: str
    is_synthetic_fraud: bool


FEATURE_NAMES = (
    "amount_minor",
    "hour_utc",
    "account_velocity_5m",
    "device_velocity_5m",
    "channel_code",
)


def extract_features(record: SyntheticRecord) -> list[float]:
    """Extract only values available at the event decision time."""

    occurred_at = datetime.fromisoformat(record["occurred_at"].replace("Z", "+00:00"))
    return [
        float(record["amount_minor"]),
        float(occurred_at.hour),
        float(record["account_velocity_5m"]),
        float(record["device_velocity_5m"]),
        float(record["channel_code"]),
    ]
