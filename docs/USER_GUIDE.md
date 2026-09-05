# User Guide

1. Edit `configs/base.yaml` to select market/credit data source, portfolio weights, rate sensitivity, model settings, limits and database behavior.
2. Run `python scripts/run_pipeline.py`.
3. Review `results/tables/` for machine-readable outputs and `results/reports/` for validation reports.
4. Launch `streamlit run dashboard/app.py` for the interactive workbench.
5. If using real data, verify `artifacts/data_provenance.json` and data-quality outputs before interpreting model results.
6. If using PostgreSQL, verify `results/tables/sql_reconciliation.csv` is fully passing.
7. Do not compare model quality from one metric alone; use coverage, independence, stability, calibration and limitations together.
