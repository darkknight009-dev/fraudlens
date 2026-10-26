"""Detector interface independent of the scoring API contract."""

from typing import Protocol


class Detector(Protocol):
    version: str

    def fit(self, features: list[list[float]]) -> None:
        """Fit only on training-time features."""

    def score(self, features: list[list[float]]) -> list[float]:
        """Return anomaly prioritization scores, not probabilities."""
