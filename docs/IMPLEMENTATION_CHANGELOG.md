# RiskSphere — Implementation Changelog

This file maps the modification blueprint to the implemented repository.

## Phase 0 — Baseline

- Original code was preserved as the starting point.
- Baseline before modification: 36 passing tests and successful synthetic market-risk pipeline.
- The original dashboard implementation is retained at `dashboard/legacy_app.py`.

## Phase 1 — Correctness

- Replaced conflicting `risk.window` / `risk.min_train_window` with one canonical `risk.training_window`.
- Added configuration validation and regression tests.
- Promoted Expected Shortfall into the standardized market-risk result table.
- Added exact result fields requested by the blueprint.
- Corrected stale EWMA/Christoffersen documentation.

## Phase 2 — Data realism

- Added source-dispatching market loader for synthetic, CSV and yfinance modes.
- Added data provenance, retrieval time, factor metadata and data-version hashing.
- Kept deterministic synthetic mode for reproducibility.

## Phase 3 — Market risk

- Preserved Historical, Parametric and EWMA VaR.
- Added GARCH(1,1) challenger using transparent SciPy QMLE.
- Added duration/convexity rate mapping and DV01.
- Extended stress contributions and portfolio attribution.
- Added risk limits, utilization and breach status.

## Phase 4 — SQL

- Added SQLAlchemy repository.
- Added PostgreSQL reference schema and SQL queries using joins, CTEs, aggregations and window functions.
- Added offline SQLite fallback for CI/demo only.
- Added Python ↔ SQL reconciliation.

## Phase 5 — Credit risk

- Added synthetic reproducible credit data, CSV mode and public OpenML `credit-g` mode.
- Added quality/leakage guards.
- Added Logistic Regression PD baseline and XGBoost challenger.
- Added ROC-AUC, KS, Brier, calibration and segment performance.
- Added transparent LGD/EAD and Expected Loss.

## Phase 6 — Credit stress

- Added baseline/moderate/severe PD/LGD stress scenarios and Expected Loss impact.

## Phase 7 — Model risk

- Added model inventory.
- Added period-by-period market stability.
- Added PSI monitoring for market factors and credit PD distribution.
- Added structured validation findings and per-model reports.

## Phase 8 — Dashboard

- Added a decision-oriented 10-page Streamlit workbench under `app/app.py`.
- `dashboard/app.py` remains the compatibility launch point.
- Dashboard can retrieve latest market-risk output from the SQL layer.

## Phase 9 — Engineering

- Expanded test suite from 36 to 49 passing tests.
- Added integration flow test and SQL reconciliation test.
- Added pipeline smoke script.
- Added structured JSON file logging.
- Added GitHub Actions CI.

## Phase 10 — Packaging

- Rewrote README for RiskSphere.
- Added architecture, methodology, data dictionary, installation, user guide, testing and limitations documents.
- `.venv`, cache directories and local DB files are excluded from the final clean package.

## Important numerical change from the original baseline

RiskSphere enables duration/convexity mapping for `RATES_10Y` by default. Therefore some market-risk numbers change from the original project. Current synthetic run:

| Model | Exceptions / 2358 | Kupiec p | Christoffersen p |
|---|---:|---:|---:|
| Historical | 32 | 0.0984 | 0.0766 |
| Parametric | 34 | 0.0431 | 0.0977 |
| EWMA | 34 | 0.0431 | 0.0977 |
| GARCH | 22 | 0.7408 | 0.5197 |

These are synthetic-run validation outputs, not claims about real-market model performance.
