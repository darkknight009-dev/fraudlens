# ML Governance and Evaluation

## Principles
- ML is a risk signal, not an oracle.
- Anomaly detection identifies unusual behavior, not necessarily fraud.
- Scores are not probabilities unless calibration is demonstrated.
- Human review remains part of the workflow.
- Model changes are versioned and evaluated before activation.

## Baseline plan
1. Create synthetic scenarios with deterministic seeds and clear provenance.
2. Define features available at the moment of scoring.
3. Exclude label, scenario name, post-event outcomes, and any future-derived data from features.
4. Split data by time and/or account/entity to reduce leakage.
5. Fit preprocessing on training data only.
6. Train a simple baseline; compare to rules-only performance.
7. Select thresholds using explicit operational goals, such as review capacity and false-positive cost.
8. Evaluate on a held-out set and report confidence/limitations.
9. Store model artifact metadata and feature schema version.
10. Test inference behavior for missing, unexpected, or out-of-range features.

## Required report
- Dataset source/provenance and license
- Synthetic vs real-data statement
- Number of rows and positive prevalence
- Feature list and point-in-time availability
- Split method and random seed
- Model and hyperparameters
- Precision, recall, F1 if useful, PR-AUC, confusion matrix, FPR/FNR
- Threshold rationale
- Baseline comparison
- Runtime and inference latency
- Limitations and known failure modes

## Drift monitoring
When implemented, monitor feature distributions, missingness, score distribution, alert rate, and confirmed outcome rate where labels become available. Do not automatically retrain and deploy without review.
