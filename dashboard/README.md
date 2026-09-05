# RiskSphere Streamlit Workbench

Launch from the repository root:

```bash
streamlit run dashboard/app.py
```

`dashboard/app.py` is a compatibility entry point that launches the new workbench in `app/app.py`.

Pages:

1. Executive Overview
2. Market Risk
3. Backtesting
4. Stress Testing
5. Reverse Stress
6. Risk Attribution
7. Credit Risk
8. Model Validation
9. Risk Limits
10. Methodology

Run `python scripts/run_pipeline.py` first so the workbench has generated tables and SQL results to display.

The previous dashboard source is preserved at `dashboard/legacy_app.py` for reference.
