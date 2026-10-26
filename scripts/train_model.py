"""Train and evaluate the reviewed baseline detector on synthetic data."""

import argparse
import json
import sys
from pathlib import Path

import joblib  # type: ignore[import-untyped]
from sklearn.metrics import (  # type: ignore[import-untyped]
    average_precision_score,
    confusion_matrix,
    precision_score,
    recall_score,
)

sys.path.insert(0, "backend")
sys.path.insert(0, ".")

from data.synthetic.generate import generate_records

from app.services.detectors.isolation_forest import IsolationForestDetector
from app.services.features import FEATURE_NAMES, extract_features


def train(seed: int, count: int, artifact: Path, report_path: Path) -> dict[str, object]:
    records = generate_records(seed, count)
    split = int(len(records) * 0.8)
    train_records, holdout = records[:split], records[split:]
    detector = IsolationForestDetector(random_state=seed)
    detector.fit([extract_features(record) for record in train_records])
    scores = detector.score([extract_features(record) for record in holdout])
    labels = [int(record["is_synthetic_fraud"]) for record in holdout]
    predictions = [int(score >= 50) for score in scores]
    artifact.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(detector, artifact)
    report: dict[str, object] = {
        "synthetic": True,
        "seed": seed,
        "rows": len(records),
        "holdout_rows": len(holdout),
        "feature_names": list(FEATURE_NAMES),
        "split": "temporal 80/20",
        "model_version": detector.version,
        "artifact": str(artifact),
        "metrics": {
            "precision": precision_score(labels, predictions, zero_division=0),
            "recall": recall_score(labels, predictions, zero_division=0),
            "pr_auc": average_precision_score(labels, scores),
            "confusion_matrix": confusion_matrix(labels, predictions).tolist(),
        },
        "governance": {
            "training_data": "synthetic only",
            "score_semantics": "prioritization index, not probability",
            "production_activation": (
                "requires explicit MODEL_ARTIFACT_PATH configuration and review"
            ),
        },
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--count", type=int, default=1_000)
    parser.add_argument(
        "--artifact", type=Path, default=Path("data/generated/fraudlens_isolation_forest.joblib")
    )
    parser.add_argument("--report", type=Path, default=Path("docs/ml_training_report.json"))
    args = parser.parse_args()
    report = train(args.seed, args.count, args.artifact, args.report)
    print(f"Trained {report['model_version']} on {report['rows']} synthetic records.")
    print(f"Artifact: {report['artifact']}")
    print(f"Report: {args.report}")


if __name__ == "__main__":
    main()
