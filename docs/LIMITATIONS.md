# Limitations

- Default market and credit datasets are synthetic.
- `yfinance` is convenient public market data, not an institutional market-data feed.
- Portfolio P&L is a factor approximation, not full instrument repricing.
- Duration/convexity is an approximation and ignores curve shape, spread, optionality and instrument-specific cash flows.
- GARCH uses Gaussian QMLE and an initial-window parameter estimate.
- Credit default definition, LGD and EAD are simplified and dataset-dependent.
- OpenML `credit-g` has no true observation date; random holdout is explicitly used in that mode.
- PSI thresholds are configurable heuristics, not universal regulatory standards.
- Risk limits are illustrative governance controls.
- SQLAlchemy/SQLite CI validation does not substitute for operational testing of a PostgreSQL deployment.
- No regulatory compliance or production readiness is claimed.
