# RiskSphere

### Financial Risk & Quantitative Analytics Platform

<p align="center">

<a href="https://risksphere-financial-risk-quantitative-analytics-platform-ku22.streamlit.app/">
  <img src="https://img.shields.io/badge/Live%20Demo-Streamlit-red?logo=streamlit" alt="Live Demo">
</a>

<a href="https://github.com/Bhardwaj-Arin/RiskSphere-Financial-Risk-Quantitative-Analytics-Platform">
  <img src="https://img.shields.io/badge/GitHub-Repository-black?logo=github" alt="GitHub">
</a>

<img src="https://img.shields.io/badge/Python-3.11+-blue?logo=python" alt="Python">

<img src="https://img.shields.io/badge/Tests-49%20Passing-success?logo=pytest" alt="Tests">

<img src="https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit" alt="Streamlit">

<img src="https://img.shields.io/badge/License-MIT-green" alt="License">

</p>

<p align="center">
  <b>An end-to-end quantitative risk analytics platform for market risk, credit risk, stress testing, model validation, portfolio attribution, risk limits, and financial risk reporting.</b>
</p>

---

## 🚀 Live Demo

### Try RiskSphere Online

👉 **[Launch the RiskSphere Dashboard](https://risksphere-financial-risk-quantitative-analytics-platform-ku22.streamlit.app/)**

No installation is required to explore the dashboard.

### Source Code

👉 **[View the RiskSphere GitHub Repository](https://github.com/Bhardwaj-Arin/RiskSphere-Financial-Risk-Quantitative-Analytics-Platform)**

---

# 📌 What is RiskSphere?

RiskSphere is an educational, industry-style financial risk analytics platform built to demonstrate how a quantitative risk workflow can move from:

**Data → Risk Models → Validation → Stress Testing → Governance → Reporting**

Instead of implementing only one risk model, the project brings multiple components of a simplified financial risk workflow together in a single platform.

It covers:

- Market Risk
- Value at Risk (VaR)
- Expected Shortfall (ES)
- VaR Backtesting
- GARCH Volatility Modelling
- Interest-Rate Risk & DV01
- Stress Testing
- Reverse Stress Testing
- Portfolio Risk Attribution
- Credit Risk
- Probability of Default (PD)
- LGD / EAD
- Expected Loss
- Model Validation
- Model Drift Monitoring
- Risk Limits
- SQL Persistence
- Interactive Streamlit Reporting

> **Project scope:** RiskSphere is an educational and portfolio project. It is not a production banking risk engine, regulatory capital calculator, or regulatory-approved risk management system.

---

# 🎯 Why was this project built?

Financial institutions need to answer questions such as:

> **How much could a portfolio lose?**

> **How reliable is the risk model?**

> **What happens under a stressed market environment?**

> **Which risk factors contribute most to portfolio risk?**

> **How much credit loss should we expect?**

> **Has model behaviour changed over time?**

> **Are risk limits being breached?**

RiskSphere attempts to demonstrate these questions through a reproducible quantitative workflow rather than treating risk modelling as an isolated machine-learning problem.

---

# 🧩 How RiskSphere Works

At a high level, the platform follows this workflow:

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