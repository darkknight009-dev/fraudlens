"""Deterministic Isolation Forest anomaly detector."""

from dataclasses import dataclass

from sklearn.ensemble import IsolationForest  # type: ignore[import-untyped]
from sklearn.preprocessing import StandardScaler  # type: ignore[import-untyped]


@dataclass
class IsolationForestDetector:
    """Baseline anomaly detector with an explicit non-probability score."""

    version: str = "isolation-forest-v1"
    random_state: int = 42
    contamination: float = "auto"  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self._scaler = StandardScaler()
        self._model = IsolationForest(
            n_estimators=100,
            contamination=self.contamination,
            random_state=self.random_state,
        )
        self._fitted = False

    def fit(self, features: list[list[float]]) -> None:
        scaled = self._scaler.fit_transform(features)
        self._model.fit(scaled)
        self._fitted = True

    def score(self, features: list[list[float]]) -> list[float]:
        if not self._fitted:
            raise RuntimeError("detector must be fitted before scoring")
        scaled = self._scaler.transform(features)
        raw = self._model.decision_function(scaled)
        # Higher means more anomalous; this is a prioritization index, not probability.
        return [max(0.0, min(100.0, float((0.5 - value) * 100))) for value in raw]
