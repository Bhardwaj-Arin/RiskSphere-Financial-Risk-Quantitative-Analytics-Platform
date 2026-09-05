# RiskSphere Architecture

```text
Market / Credit / Stress Data
            ↓
Ingestion + Provenance
            ↓
Data Quality + Leakage Checks
            ↓
 ┌────────────────┬─────────────────┬────────────────┐
 │ Market Risk    │ Credit Risk     │ Portfolio      │
 │ VaR / ES       │ PD / LGD / EAD  │ Mapping        │
 │ EWMA / GARCH   │ Expected Loss   │ Attribution    │
 │ Backtesting    │ Credit Stress   │ Rate DV01      │
 └────────────────┴─────────────────┴────────────────┘
            ↓
Stress / Reverse Stress
            ↓
Validation + Drift + Stability
            ↓
Limits + Model Inventory + Findings
            ↓
SQL Persistence + Reconciliation
            ↓
Streamlit Risk Workbench + Reports
```

## Design principles

1. **Configuration-driven:** market confidence, horizon, training window, data sources, limits, rate mapping, credit assumptions and monitoring thresholds live in `configs/base.yaml`.
2. **No silent look-ahead:** forecast date `t` uses information available strictly before `t`.
3. **Source lineage:** every market dataset receives provenance metadata and a data-version hash.
4. **Challenger discipline:** GARCH and XGBoost are alternatives to compare, not automatic winners.
5. **Persistence is a control:** generated outputs are stored in SQL and reconciled back to Python totals.
6. **Governance is explicit:** model inventory, validation findings, drift and limit status are data products, not prose-only claims.
7. **Scope is bounded:** no claim of production-bank infrastructure or regulatory compliance.
