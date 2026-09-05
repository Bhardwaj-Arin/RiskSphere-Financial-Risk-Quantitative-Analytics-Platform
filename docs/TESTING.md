# Testing and Validation

Run:

```bash
pytest -q
python scripts/run_pipeline.py
python -m py_compile app/app.py dashboard/app.py
```

Tests cover original portfolio/VaR/stress functionality plus:

- canonical configuration behavior
- unified VaR/ES contract
- source-driven ingestion and provenance
- GARCH parameter/stationarity checks
- no-look-ahead behavior for the first GARCH OOS forecast
- duration/DV01 calculations
- credit PD/Expected Loss/stress flow
- risk-limit status
- SQL persistence and Python↔SQL reconciliation

GitHub Actions executes the tests, a full pipeline smoke run, and Streamlit syntax checks.
