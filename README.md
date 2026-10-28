# ◈ RiskSphere

### Financial Risk & Quantitative Analytics Platform

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit-red?logo=streamlit)](https://risksphere-financial-risk-quantitative-analytics-platform-ku22.streamlit.app/)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-black?logo=github)](https://github.com/Bhardwaj-Arin/RiskSphere-Financial-Risk-Quantitative-Analytics-Platform)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-49%20passing-success?logo=pytest)](tests)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit)](dashboard/app.py)
[![CI](https://github.com/Bhardwaj-Arin/RiskSphere-Financial-Risk-Quantitative-Analytics-Platform/actions/workflows/ci.yml/badge.svg)](https://github.com/Bhardwaj-Arin/RiskSphere-Financial-Risk-Quantitative-Analytics-Platform/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-MIT-green)](#license)

**An end-to-end quantitative risk analytics platform covering market risk, credit risk, stress testing, model validation, portfolio attribution, risk limits, SQL persistence, and an interactive 8-page storytelling dashboard.**

👉 **[Launch the Live Dashboard](https://risksphere-financial-risk-quantitative-analytics-platform-ku22.streamlit.app/)** &nbsp;|&nbsp; 📄 **[Read the Full Project Report (PDF)](RiskForge-QRM_Project_Report.pdf)**

<!-- After you add screenshots to docs/screenshots/, remove the comment markers around the image lines below -->
<!--
![RiskSphere dashboard home](docs/screenshots/home.png)
-->

---

## Table of Contents

1. [Overview](#overview)
2. [Why This Project Exists](#why-this-project-exists)
3. [Key Results at a Glance](#key-results-at-a-glance)
4. [Key Features](#key-features)
5. [System Architecture](#system-architecture)
6. [Tech Stack](#tech-stack)
7. [Project Structure](#project-structure)
8. [Methodology](#methodology)
9. [Getting Started](#getting-started)
10. [Configuration](#configuration)
11. [Dashboard Walkthrough](#dashboard-walkthrough)
12. [Testing & CI](#testing--ci)
13. [Sample Outputs](#sample-outputs)
14. [Limitations & Scope](#limitations--scope)
15. [Roadmap](#roadmap)
16. [Author](#author)
17. [License](#license)

---

## Overview

RiskSphere is an **educational, industry-style financial risk analytics platform** built to demonstrate how a real quantitative risk workflow moves end-to-end:

> **Data → Risk Models → Validation → Stress Testing → Governance → Reporting**

Rather than implementing a single risk model in isolation, RiskSphere wires together the pieces a bank's market-risk and credit-risk desks actually rely on — VaR/ES engines, backtesting, GARCH volatility modelling, credit scoring, stress testing, model governance, SQL persistence, and an interactive dashboard — into one coherent, configuration-driven, tested codebase.

> **Scope statement:** RiskSphere is a portfolio/learning project. It is **not** a production banking risk engine, a regulatory capital calculator, or a Basel/CCAR/OCC/PRA/IFRS 9/CECL-compliant system. See [Limitations & Scope](#limitations--scope).

## Why This Project Exists

Risk functions at financial institutions are ultimately trying to answer a small set of hard questions:

- How much could this portfolio lose, and how reliable is that estimate?
- Is the risk model actually working, or has it silently drifted?
- What happens to the book under a stressed market environment?
- Which risk factors are driving portfolio risk?
- How much credit loss should we expect, and how does that change under stress?
- Are we inside our risk limits, and can we prove it?

RiskSphere was built to demonstrate a **reproducible, auditable workflow** that answers these questions — instead of treating "risk modelling" as a single isolated ML task with one metric and no governance around it.

## Key Results at a Glance

All results below come from the reproducible synthetic dataset (fixed seed), a 5-factor portfolio of 1,000,000 notional, and a 99% / 1-day risk setting. Re-run `python scripts/run_pipeline.py` to regenerate them.

| Area | Result |
|---|---|
| **Market risk (VaR)** | Latest 1-day 99% VaR ranges from 1.46% to 2.28% of the portfolio depending on the model (GARCH is the most cautious at about 22,800 per 1,000,000) |
| **Backtesting** | GARCH(1,1) breached its VaR on 0.93% of 2,358 out-of-sample days (target 1%) and passed both the Kupiec and Christoffersen tests. Parametric and EWMA breached on 1.44% of days and **failed** the Kupiec test (they assume a bell curve and understate crashes) |
| **Risk attribution** | The equity index is 45% of the money but about 70% of portfolio variance. Gold has a slightly negative contribution, so it acts as a natural hedge |
| **Stress testing** | The worst configured scenario (2008-style equity crash) costs about 9.0% of the portfolio, roughly 3.9× the normal-day VaR |
| **Reverse stress** | The minimum-size shock that loses 10% was found from 6 different starting points and converged to the same answer each time |
| **Credit risk** | Expected loss is about 1.50M on 20.75M lent (7.2%). A severe recession scenario raises it by about 118% |
| **PD models** | Logistic Regression ranks borrowers slightly better (AUC 0.755 vs 0.730), but XGBoost gives far better-calibrated probabilities (Brier 0.101 vs 0.203), so XGBoost feeds the Expected Loss calculation |
| **Governance** | The credit expected-loss limit is breached at 181% utilisation. The system raises it automatically as a HIGH finding. The GOLD input also triggers a PSI drift warning (0.154) |
| **Engineering** | 49 automated tests, GitHub Actions CI, SQL persistence, and Python ↔ SQL reconciliation with zero differences |

## Key Features

**Market Risk**
- Historical, Parametric, and EWMA Value-at-Risk (VaR)
- Expected Shortfall (ES) for every VaR methodology
- GARCH(1,1) volatility modelling (Gaussian QMLE) as a challenger model
- Strictly out-of-sample, no-look-ahead forecasting
- Interest-rate risk via duration/convexity and DV01
- Model comparison across all VaR methodologies

**Model Validation**
- VaR backtesting via Kupiec (unconditional coverage) and Christoffersen (independence) tests
- Population Stability Index (PSI) for input/feature drift monitoring
- Model stability checks across time windows

**Stress Testing**
- Configurable historical-style and hypothetical stress scenarios (equity crash, rate shock, oil supply shock, FX crisis)
- Reverse stress testing — solves for the minimum-norm shock vector that reaches a target loss
- Portfolio risk attribution by factor and by scenario

**Credit Risk**
- Probability of Default (PD) via Logistic Regression baseline + XGBoost challenger
- Model diagnostics: ROC-AUC, KS statistic, Brier score, calibration, segment performance
- Expected Loss = PD × LGD × EAD
- Credit stress testing across baseline / moderate / severe scenarios

**Governance & Persistence**
- Model inventory (purpose, target, data, assumptions, limitations, version, validation status)
- Rule-based risk limits with utilization and breach status
- Structured validation findings generated from backtesting/drift/limit rules
- SQLAlchemy persistence layer (SQLite offline demo, PostgreSQL production-style mode)
- Automated Python ↔ SQL reconciliation

**Reporting & Dashboard**
- Interactive 8-page Streamlit dashboard that explains every concept in plain English and shows results as live Plotly charts
- A "Build Your Own Crash" stress lab: drag sliders for each risk factor and watch the portfolio loss update instantly
- Takeaways and headline numbers are generated from the result files, so they stay correct whenever the pipeline is re-run
- Multiple data source modes: synthetic (deterministic, seeded), CSV, or live `yfinance` market data
- Full data provenance and data-quality/leakage checks on every ingested dataset

## System Architecture

```text
               DATA SOURCES
                    │
       ┌────────────┼────────────┐
       │            │            │
       ▼            ▼            ▼
   Synthetic       CSV        yfinance
       │
       └────────────┬────────────┘
                    ▼
           DATA INGESTION
                    │
                    ▼
        DATA QUALITY & PROVENANCE
                    │
       ┌────────────┴────────────┐
       │                         │
       ▼                         ▼
 MARKET RISK                CREDIT RISK
       │                         │
 ┌─────┼─────┐             ┌─────┼─────┐
 │     │     │             │     │     │
VaR    ES   GARCH          PD   LGD   EAD
 │     │     │              │     │     │
 └─────┼─────┘              └─────┼─────┘
       │                          │
       └────────────┬─────────────┘
                    ▼
          STRESS & SCENARIO ANALYSIS
                    │
                    ▼
          MODEL VALIDATION & MONITORING
                    │
                    ▼
            RISK GOVERNANCE
                    │
       ┌────────────┴────────────┐
       ▼                         ▼
 SQL PERSISTENCE          STREAMLIT DASHBOARD
```

**Design principles** (from [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)):

| Principle | What it means in this codebase |
|---|---|
| Configuration-driven | Confidence level, horizon, training window, data source, limits, rate mapping and credit assumptions all live in `configs/base.yaml` — no hard-coded parameters in the model code |
| No silent look-ahead | Every forecast for date `t` uses only information available strictly before `t` |
| Source lineage | Every market dataset gets provenance metadata and a data-version hash (`artifacts/data_provenance.json`) |
| Challenger discipline | GARCH and XGBoost are compared against baselines, never assumed to be automatic winners |
| Persistence as a control | Every pipeline run's outputs are written to SQL and reconciled back against the Python totals |
| Explicit governance | Model inventory, validation findings, drift and limit status are structured data products, not prose claims |
| Bounded scope | No claim of production-bank infrastructure or regulatory compliance |

## Tech Stack

| Layer | Tools |
|---|---|
| Language | Python 3.11+ |
| Numerical / Stats | NumPy, pandas, SciPy, statsmodels |
| Machine Learning | scikit-learn, XGBoost |
| Market Data | yfinance |
| Persistence | SQLAlchemy, SQLite (offline demo), PostgreSQL (`psycopg2-binary`) |
| Dashboard / Viz | Streamlit, Plotly, Matplotlib |
| Config | PyYAML, python-dotenv |
| Testing / CI | pytest, GitHub Actions |

## Project Structure

```text
RiskSphere/
├── app/                     # Streamlit dashboard (8-page storytelling app)
├── dashboard/               # Compatibility wrapper for `streamlit run dashboard/app.py`
├── .streamlit/              # Dashboard theme (config.toml)
├── src/riskforge/           # Core Python package
│   ├── data/                #   loading, synthetic generation, data-quality checks
│   ├── models/              #   Historical / Parametric / EWMA VaR, Expected Shortfall
│   ├── market_risk/         #   GARCH, rates/DV01, unified market-risk service
│   ├── credit_risk/         #   PD/LGD/EAD models, features, stress, service layer
│   ├── portfolio/           #   portfolio engine (factor → P&L mapping)
│   ├── attribution/         #   risk attribution by factor / scenario
│   ├── stress/              #   scenario shocks + reverse stress solver
│   ├── validation/          #   backtesting (Kupiec/Christoffersen), drift, stability
│   ├── governance/          #   model inventory, risk limits
│   ├── database/            #   SQLAlchemy repository + reconciliation
│   ├── reporting/           #   report generation
│   └── utils/               #   config loader, logging, reproducibility (seeding)
├── configs/                 # base.yaml (all model/portfolio/limit parameters), stress_scenarios.yaml
├── sql/                     # schema.sql (PostgreSQL DDL), risk_queries.sql, data_quality.sql
├── scripts/                 # run_pipeline.py (end-to-end run), smoke_test.py
├── tests/                   # 49 pytest unit/integration tests
├── results/                 # generated tables (results/tables), figures, reports
├── artifacts/               # provenance JSON, run logs, local SQLite DB
├── docs/                    # architecture, methodology, installation, testing, limitations, interview notes
└── RiskForge-QRM_Project_Report.pdf   # full written project report
```

## Methodology

Full detail lives in [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md); the essentials:

**Market risk representation.** Price-like factors use simple percentage returns; the 10-year rate factor is an absolute yield change. When rate-duration mapping is enabled, the yield move is converted to a bond-return proxy:

```
ΔP/P ≈ -D · Δy + 0.5 · C · (Δy)²
```

DV01 is the first-order currency sensitivity: `Notional × Duration × 0.0001`.

**VaR / Expected Shortfall.** All market forecasts are one-step-ahead and strictly out-of-sample.
- *Historical VaR* — empirical lower quantile of the trailing training window
- *Parametric VaR* — trailing mean/std with a normal quantile
- *EWMA* — recursive conditional variance with a configured decay factor
- *GARCH(1,1)* — Gaussian QMLE fit on the initial training window, then recursed out-of-sample as a challenger model

Expected Shortfall is the average historical tail loss (Historical VaR) or the conditional-normal tail expectation (Parametric/EWMA/GARCH).

**Backtesting.** An exception occurs when the realized loss exceeds the VaR forecast. The **Kupiec test** checks whether the exception rate matches the target confidence level; the **Christoffersen test** checks whether exceptions are independent over time (i.e., not clustered). The two are reported and interpreted separately.

**Stress & reverse stress.** Configured factor shocks flow through the same portfolio mapping used elsewhere in the pipeline. Reverse stress testing solves for the minimum-L2-norm shock vector that reaches a configured target loss within factor bounds — a constrained scenario under the model, not a claim about the "true" worst case.

**Credit Expected Loss.** PD is estimated via a Logistic Regression baseline and an XGBoost challenger, evaluated on ROC-AUC, KS statistic, Brier score, calibration, and segment performance. `Expected Loss = PD × LGD × EAD`, with LGD/EAD as transparent, simplified assumptions (documented, not hidden). Credit stress scales PD and shifts LGD under configured scenarios.

**Monitoring & governance.** PSI compares reference vs. current feature distributions to flag drift. Risk limits report value/limit/utilization/status. The model inventory records purpose, target, data, assumptions, limitations, version, and validation status for every model. Findings are auto-generated from backtesting, drift, and limit-breach rules.

## Getting Started

### Prerequisites
- Python 3.11+

### Installation & Offline Demo

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q

python scripts/run_pipeline.py   # runs the full pipeline against deterministic synthetic data
streamlit run dashboard/app.py   # launches the 8-page dashboard
```

The offline demo uses deterministic, seeded synthetic market and credit data plus a local SQLite database — no external services or credentials required.

### PostgreSQL Mode (production-style)

```bash
# apply sql/schema.sql if you want to inspect the reference DDL directly
export RISKQUANT_DATABASE_URL='postgresql+psycopg2://user:password@host:5432/riskquant'
python scripts/run_pipeline.py
```

The SQLAlchemy repository can also create the required tables automatically. **Never commit real database credentials** — use `.env` (see `.env.example`) and keep it out of version control.

## Configuration

Everything about a run is controlled from [`configs/base.yaml`](configs/base.yaml) — no parameters are hard-coded in the model logic:

- **Data source**: `synthetic | csv | yfinance`, date range, risk factors (`EQUITY_INDEX`, `RATES_10Y`, `FX_USD`, `OIL`, `GOLD`), tickers, and a fixed random seed for reproducibility
- **Portfolio**: notional, per-factor weights, and rate-duration mapping (duration/convexity)
- **Risk**: confidence level (default 99%), horizon (1 day), training window (250 observations)
- **Models**: EWMA decay (λ = 0.94), GARCH(1,1) settings
- **Stress**: target loss and per-factor shock bounds for reverse stress ([`configs/stress_scenarios.yaml`](configs/stress_scenarios.yaml) holds the named historical-style scenarios)
- **Limits**: VaR/ES/stress-loss/credit-EL thresholds
- **Credit**: data source (`synthetic | csv | openml_credit_g`), sample size, LGD baseline, challenger model, and a 3-tier credit stress ladder (baseline/moderate/severe)
- **Monitoring**: PSI bin count and warning/breach thresholds
- **Database**: SQLite fallback URL, with `RISKQUANT_DATABASE_URL` overriding to PostgreSQL

## Dashboard Walkthrough

The dashboard (`app/app.py`) is built so a first-time visitor can understand the project in about two minutes. Every page explains the concept in plain English, shows the result as an interactive chart, and ends with a takeaway. The sidebar navigates between 8 pages:

| Page | What you see |
|---|---|
| 🏠 Start Here | The 30-second story (problem, what was built, what was found), a pipeline diagram, 8 headline result cards, a portfolio chart and key findings |
| 📉 Market Risk | VaR and Expected Shortfall in dollars for any portfolio size, a forecast-vs-actual chart with breaches marked, GARCH volatility, and all four models side by side |
| ✅ Backtesting | A pass/fail report card per model (Kupiec and Christoffersen), breach counts vs. expected, p-value chart, and a year-by-year breach-rate heatmap |
| 💥 Stress Testing | Scenario losses, a waterfall showing which asset caused the loss, the **Build Your Own Crash** slider lab, and a reverse stress test |
| 🧩 Risk Attribution | Share of money invested vs. share of risk for each asset |
| 🏦 Credit Risk | Expected Loss = PD × LGD × EAD with real numbers, loss by loan size, ROC curves, a calibration chart and a recession simulator |
| 🛡️ Governance | Risk-limit gauges, validation findings, PSI drift monitoring, model inventory and Python ↔ SQL reconciliation |
| 📖 About & Method | Tech stack, methodology with formulas, and honest limitations |

<!-- After you add screenshots to docs/screenshots/, remove the comment markers around the image lines below -->
<!--
![Market risk page](docs/screenshots/market_risk.png)
![Stress lab](docs/screenshots/stress_lab.png)
-->

## Testing & CI

```bash
pytest -q
python scripts/run_pipeline.py
python -m py_compile app/app.py dashboard/app.py
```

**49 automated tests** cover, among other things:
- canonical configuration behavior and the unified VaR/ES contract
- source-driven ingestion and data provenance
- GARCH parameter/stationarity checks and no-look-ahead behavior for the first out-of-sample forecast
- duration/DV01 calculations
- the full credit PD → Expected Loss → stress flow
- risk-limit status logic
- SQL persistence and Python ↔ SQL reconciliation

GitHub Actions ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) runs the full test suite, an end-to-end pipeline smoke run, and a Streamlit syntax check on every push and pull request.

## Sample Outputs

Every pipeline run writes machine-readable outputs to `results/tables/` (e.g. `market_risk_results.csv`, `credit_expected_loss.csv`, `backtest_*_var.csv`, `stress_scenarios.csv`, `risk_limits.csv`, `sql_reconciliation.csv`) and validation reports to `results/reports/`, so every number shown in the dashboard can be traced back to a concrete artifact on disk. The full write-up, including methodology discussion and results interpretation, is in [`RiskForge-QRM_Project_Report.pdf`](RiskForge-QRM_Project_Report.pdf).

## Limitations & Scope

Documented in full in [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md) — stated up front rather than discovered later:

- Default market and credit datasets are synthetic; `yfinance` is convenient public data, not an institutional feed
- Portfolio P&L is a factor approximation, not full instrument repricing
- Duration/convexity ignores curve shape, spread, optionality, and instrument-specific cash flows
- GARCH uses Gaussian QMLE with an initial-window parameter estimate
- Credit default definition, LGD and EAD are simplified and dataset-dependent
- PSI thresholds are configurable heuristics, not regulatory standards
- Risk limits are illustrative governance controls, not live enterprise limits
- **No regulatory compliance or production readiness is claimed anywhere in this project**

## Roadmap

- Live PostgreSQL deployment validation (currently implemented and unit-tested against SQLite; see [`docs/IMPLEMENTATION_STATUS.md`](docs/IMPLEMENTATION_STATUS.md))
- Additional volatility models (EGARCH/GJR-GARCH) as further challengers
- Expanded credit segment reporting and vintage analysis
- Embedded dashboard screenshots/GIFs in this README (see `docs/screenshots/README.md` for the capture process)

## Author

**Arin Bhardwaj**
M.Sc. Mathematics & Scientific Computing, NIT Warangal
GitHub: [@Bhardwaj-Arin](https://github.com/Bhardwaj-Arin)

Interview-oriented notes on design decisions and trade-offs made while building this project are collected in [`docs/INTERVIEW_NOTES.md`](docs/INTERVIEW_NOTES.md).

## License

Released under the [MIT License](LICENSE).