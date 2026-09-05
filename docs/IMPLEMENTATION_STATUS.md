# RiskSphere — Implementation Status

## Implemented and locally validated

- Original Historical, Parametric and EWMA VaR preserved.
- Expected Shortfall fully surfaced in unified results.
- Strictly out-of-sample market backtesting preserved.
- Stress, reverse stress and attribution run successfully.
- Canonical 250-observation training-window configuration implemented.
- Synthetic, CSV and yfinance market-data modes implemented with provenance.
- GARCH(1,1), duration/convexity, DV01, limits and breach detection implemented.
- Credit PD/LGD/EAD/Expected Loss pipeline implemented.
- Logistic baseline and XGBoost challenger implemented with calibration/segment metrics.
- Credit stress by portfolio and segment implemented.
- Model inventory, stability, PSI and structured findings implemented.
- SQLAlchemy persistence and retrieval implemented.
- Python↔SQL reconciliation implemented and passes on the offline SQLite backend.
- PostgreSQL DDL/queries and SQLAlchemy connection path implemented.
- 10-page decision-oriented Streamlit workbench implemented.
- 49 automated tests pass.
- End-to-end pipeline and smoke check pass.
- GitHub Actions CI included.
- Documentation and example outputs included.

## Environment-limited validation

### PostgreSQL runtime

No PostgreSQL server is installed in the execution environment used to build this package. PostgreSQL connection support and reference DDL are implemented, but the live end-to-end run here used the SQLite fallback. Before claiming a PostgreSQL deployment, run the pipeline with `RISKQUANT_DATABASE_URL` pointing to a real PostgreSQL instance and verify `sql_reconciliation.csv`.

### Internet-backed real market/public credit data

The build environment is offline. `yfinance` market mode and OpenML `credit-g` mode are implemented, while synthetic and CSV workflows are the modes locally exercised. Before making real-data claims, run these modes with actual sourced data and preserve the generated provenance.

### Streamlit screenshots

The build environment does not have Streamlit installed, so the workbench source was syntax-checked rather than launched here. Screenshot instructions are in `docs/screenshots/README.md`. Do not use a mock screenshot as evidence of a deployed dashboard.
