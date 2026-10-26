"""Generate deterministic, clearly synthetic fraud scenarios."""

import argparse
import csv
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.services.features import SyntheticRecord


def generate_records(seed: int = 42, count: int = 200) -> list[SyntheticRecord]:
    rng = random.Random(seed)
    start = datetime(2026, 1, 1, tzinfo=UTC)
    records: list[SyntheticRecord] = []
    for index in range(count):
        anomalous = index % 5 == 0
        amount = rng.randint(100, 10_000) if not anomalous else rng.randint(100_000, 2_000_000)
        account_velocity = rng.randint(0, 4) if not anomalous else rng.randint(12, 30)
        device_velocity = rng.randint(0, 3) if not anomalous else rng.randint(10, 25)
        occurred_at = start + timedelta(minutes=index * 7)
        records.append(
            {
                "transaction_id": f"synthetic_{index:05d}",
                "amount_minor": amount,
                "occurred_at": occurred_at.isoformat().replace("+00:00", "Z"),
                "account_velocity_5m": account_velocity,
                "device_velocity_5m": device_velocity,
                "channel_code": rng.randint(0, 3),
                "scenario": "synthetic_anomalous" if anomalous else "synthetic_normal",
                "is_synthetic_fraud": anomalous,
            }
        )
    return records


def write_csv(records: list[SyntheticRecord], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--count", type=int, default=200)
    parser.add_argument(
        "--output", type=Path, default=Path("data/generated/synthetic_transactions.csv")
    )
    args = parser.parse_args()
    write_csv(generate_records(args.seed, args.count), args.output)
    print(f"Wrote synthetic dataset to {args.output} using seed {args.seed}.")


if __name__ == "__main__":
    main()
