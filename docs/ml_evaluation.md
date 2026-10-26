# Synthetic ML Evaluation

Run `make synthetic-evaluate` to regenerate `docs/ml_evaluation_report.json`.

The report uses a deterministic seed and a temporal 80/20 holdout. Features are limited to values available at scoring time; scenario names and synthetic labels are excluded. The Isolation Forest score is an anomaly-prioritisation index, not a calibrated fraud probability. Synthetic results must not be presented as production performance.
