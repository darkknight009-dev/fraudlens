from pathlib import Path

from data.synthetic.generate import generate_records
from scripts.train_model import train

from app.core.config import Settings
from app.services.detectors.isolation_forest import IsolationForestDetector
from app.services.features import FEATURE_NAMES, extract_features
from app.services.ml_runtime import load_detector


def test_synthetic_generation_is_reproducible_and_labeled() -> None:
    first = generate_records(seed=7, count=20)
    second = generate_records(seed=7, count=20)

    assert first == second
    assert all(record["is_synthetic_fraud"] in {True, False} for record in first)
    assert "scenario" not in FEATURE_NAMES
    assert len(extract_features(first[0])) == len(FEATURE_NAMES)


def test_isolation_forest_is_deterministic_and_requires_fit() -> None:
    records = generate_records(seed=42, count=50)
    features = [extract_features(record) for record in records]
    detector = IsolationForestDetector(random_state=42)
    try:
        detector.score(features)
    except RuntimeError:
        pass
    else:
        raise AssertionError("unfitted detector returned scores")

    detector.fit(features[:40])
    first = detector.score(features[40:])
    second_detector = IsolationForestDetector(random_state=42)
    second_detector.fit(features[:40])
    second = second_detector.score(features[40:])
    assert first == second
    assert all(0 <= score <= 100 for score in first)


def test_training_writes_reviewable_artifact(tmp_path: Path) -> None:
    artifact = tmp_path / "model.joblib"
    report = tmp_path / "report.json"

    result = train(seed=42, count=100, artifact=artifact, report_path=report)

    assert artifact.is_file()
    assert report.is_file()
    assert result["model_version"] == "isolation-forest-v1"
    detector, version = load_detector(
        Settings(
            app_env="test",
            api_key_hash_pepper="test-pepper-with-at-least-32-characters",
            model_artifact_path=str(artifact),
        )
    )
    assert detector is not None
    assert version == "isolation-forest-v1"
