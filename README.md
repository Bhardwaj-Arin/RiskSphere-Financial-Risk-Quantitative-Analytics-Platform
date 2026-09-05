# RiskSphere

## Financial Risk & Quantitative Analytics Platform

RiskSphere is an educational, industry-style financial risk analytics platform designed to demonstrate an end-to-end quantitative risk workflow.

The platform extends the original RiskForge-QRM market-risk prototype into a broader risk analytics system covering **market risk, credit risk, stress testing, reverse stress testing, portfolio risk attribution, model validation, risk limits, SQL persistence, monitoring, and decision-oriented reporting through Streamlit**.

> **Scope & Disclaimer:** RiskSphere is an educational and portfolio project. It is not a production banking risk engine, regulatory capital calculator, Basel/CCAR/OCC/PRA-approved system, or IFRS 9/CECL implementation. Results are dependent on the underlying data, modelling assumptions, configuration, and methodology.

---

## Key Capabilities

### Market Risk

- Source-driven market data pipeline supporting:
  - Deterministic synthetic data
  - CSV-based data
  - `yfinance` market data
- Explicit factor mapping for:
  - Equity
  - 10Y interest rates
  - USD FX
  - Oil
  - Gold
- Duration/convexity approximation for the interest-rate factor
- DV01 reporting
- One-day, 99% out-of-sample VaR using:
  - Historical Simulation
  - Normal Parametric VaR
  - EWMA
  - GARCH(1,1) challenger
- Expected Shortfall (ES) for every market-risk model
- Standardized market-risk result contract containing:
  - Model
  - Confidence level
  - Horizon
  - VaR
  - Expected Shortfall
  - Forecast date
  - Realized return
  - Exception flag
  - Training window
  - Data version

### Backtesting & Model Validation

- Out-of-sample VaR backtesting
- Kupiec unconditional coverage test
- Christoffersen independence test
- Model comparison across competing VaR methodologies
- Period stability analysis
- PSI-based distribution drift monitoring
- Calibration and segment-level credit model evaluation
- Structured validation findings with severity, evidence, recommendation, and status

### Stress & Scenario Analysis

- Configurable market stress scenarios
- Sensitivity analysis
- Reverse stress testing
- Factor-level risk attribution
- Portfolio-level stress loss analysis
- Credit stress scenarios across baseline, moderate, and severe conditions

### Credit Risk

- Deterministic synthetic credit-data workflow
- CSV-based credit-data workflow
- Optional OpenML credit-data mode
- Data-quality and leakage checks
- Logistic Regression PD baseline
- XGBoost PD challenger
- Model evaluation using:
  - ROC-AUC
  - KS statistic
  - Brier score
  - Calibration
  - Segment performance
- Transparent LGD and EAD assumptions
- Expected Loss calculation:

$$
\text{Expected Loss} = PD \times LGD \times EAD
$$

- Credit Expected Loss stress testing

### Risk Governance

- Model inventory
- Model version and methodology tracking
- Period stability monitoring
- PSI drift monitoring
- Risk limits
- Limit utilization
- Breach detection
- Validation warnings and findings

### Data & Database Layer

- SQLAlchemy-based persistence layer
- PostgreSQL deployment path
- SQLite fallback for offline development and CI
- Python ↔ SQL reconciliation checks
- Data provenance metadata including:
  - Data source
  - Retrieval timestamp
  - Factor metadata
  - Row count
  - Date range
  - Deterministic data-version hash

### Interactive Risk Workbench

The Streamlit application provides dedicated pages for:

1. Executive Overview
2. Market Risk
3. Backtesting
4. Stress Testing
5. Reverse Stress Testing
6. Risk Attribution
7. Credit Risk
8. Model Validation
9. Risk Limits
10. Methodology

---

# Current Validated Offline Run

The repository defaults to **deterministic synthetic market and credit data**, allowing the complete workflow to run without internet access.

The following results are therefore **demonstration outputs rather than real-market or real-loan findings**.

## Market VaR Backtesting

| Model | Exceptions | Exception Rate | Kupiec p-value | Christoffersen p-value | Result |
|---|---:|---:|---:|---:|---|
| Historical VaR | 32 / 2358 | 1.357% | 0.0984 | 0.0766 | Pass |
| Parametric VaR | 34 / 2358 | 1.442% | 0.0431 | 0.0977 | Coverage finding |
| EWMA VaR | 34 / 2358 | 1.442% | 0.0431 | 0.0977 | Coverage finding |
| GARCH VaR | 22 / 2358 | 0.933% | 0.7408 | 0.5197 | Pass |

The results differ from the original RiskForge-QRM baseline because RiskSphere activates the updated duration/convexity mapping for the 10-year rate factor.

The historical model retains 32 exceptions, while the Parametric and EWMA results change. This is an intentional modelling change rather than an undocumented baseline drift.

> **Important:** GARCH passing the two statistical tests in this synthetic demonstration does **not** establish that GARCH is universally superior to EWMA or Parametric VaR.

---

## Credit Risk Demonstration

The default synthetic credit workflow produces an observed holdout default rate of approximately **12.7%**.

Logistic Regression and XGBoost are evaluated side-by-side using multiple performance and calibration metrics. The challenger model is **not automatically declared the winner** solely because it is more complex.

The configured credit Expected Loss limit is intentionally evaluated by the governance layer. The current synthetic run produces a limit breach, which is surfaced by the system rather than suppressed.

This demonstrates an important risk-management principle:

> A risk analytics system should expose adverse findings rather than optimize its output to make the model or portfolio appear healthier.

---

# Architecture

```text
                    ┌──────────────────────────┐
                    │       Data Sources       │
                    │                          │
                    │ Synthetic / CSV /        │
                    │ yfinance / OpenML        │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │   Data Ingestion & DQ    │
                    │                          │
                    │ Cleaning / Validation /  │
                    │ Provenance / Versioning   │
                    └────────────┬─────────────┘
                                 │
              ┌──────────────────┴──────────────────┐
              │                                     │
              ▼                                     ▼
   ┌──────────────────────┐              ┌──────────────────────┐
   │     Market Risk      │              │     Credit Risk      │
   │                      │              │                      │
   │ VaR / ES / GARCH     │              │ PD / LGD / EAD / EL  │
   │ Rates / DV01         │              │ Model Validation     │
   └──────────┬───────────┘              └──────────┬───────────┘
              │                                     │
              └──────────────────┬──────────────────┘
                                 ▼
                    ┌──────────────────────────┐
                    │ Stress & Scenario Engine │
                    │                          │
                    │ Stress / Reverse Stress │
                    │ Attribution              │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Validation & Governance  │
                    │                          │
                    │ Backtesting / Drift      │
                    │ Limits / Findings        │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
          ┌──────────────────┐       ┌──────────────────┐
          │ SQL Persistence  │       │ Streamlit        │
          │                  │       │ Risk Workbench   │
          │ SQLite/Postgres  │       │                  │
          └──────────────────┘       └──────────────────┘