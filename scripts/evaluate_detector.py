"""Evaluate the baseline detector on a deterministic held-out synthetic set."""

import json
import sys
from pathlib import Path

from sklearn.metrics import average_precision_score, confusion_matrix, precision_score, recall_score

sys.path.insert(0, "backend")
sys.path.insert(0, ".")

from data.synthetic.generate import generate_records

from app.services.detectors.isolation_forest import IsolationForestDetector
from app.services.features import extract_features


def evaluate(seed: int = 42, count: int = 200) -> dict[str, object]:
    records = generate_records(seed, count)
    split = int(len(records) * 0.8)
    train, holdout = records[:split], records[split:]
    detector = IsolationForestDetector(random_state=seed)
    detector.fit([extract_features(record) for record in train])
    scores = detector.score([extract_features(record) for record in holdout])
    labels = [int(record["is_synthetic_fraud"]) for record in holdout]
    predictions = [int(score >= 50) for score in scores]
    return {
        "synthetic": True,
        "seed": seed,
        "rows": len(records),
        "holdout_rows": len(holdout),
        "positive_prevalence": sum(labels) / len(labels),
        "feature_names": [
            "amount_minor",
            "hour_utc",
            "account_velocity_5m",
            "device_velocity_5m",
            "channel_code",
        ],
        "split": "temporal 80/20",
        "model_version": detector.version,
        "metrics": {
            "precision": precision_score(labels, predictions, zero_division=0),
            "recall": recall_score(labels, predictions, zero_division=0),
            "pr_auc": average_precision_score(labels, scores),
            "confusion_matrix": confusion_matrix(labels, predictions).tolist(),
        },
        "limitations": [
            "Synthetic anomaly labels are not production fraud outcomes.",
            "Isolation Forest scores are prioritization indices, not calibrated probabilities.",
        ],
    }


def main() -> None:
    report = evaluate()
    destination = Path("docs/ml_evaluation_report.json")
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {destination}")


if __name__ == "__main__":
    main()
