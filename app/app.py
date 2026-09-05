"""RiskSphere decision-oriented Streamlit risk workbench."""
from __future__ import annotations

from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import streamlit as st
import plotly.express as px

from riskforge.utils.config import load_config
from riskforge.database import RiskRepository, database_url

RESULTS = ROOT / "results" / "tables"


def load_table(name: str) -> pd.DataFrame:
    p = RESULTS / f"{name}.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


def pct(x: float) -> str:
    return f"{x:.2%}"


def main() -> None:
    st.set_page_config(page_title="RiskSphere", page_icon="◈", layout="wide")
    cfg = load_config("base.yaml")
    st.sidebar.title("◈ RiskSphere")
    st.sidebar.caption("Financial Risk & Quantitative Analytics Platform")
    pages = ["Executive Overview", "Market Risk", "Backtesting", "Stress Testing",
             "Reverse Stress", "Risk Attribution", "Credit Risk", "Model Validation",
             "Risk Limits", "Methodology"]
    page = st.sidebar.radio("Navigate", pages)
    st.sidebar.caption("Educational, industry-style portfolio project — not regulatory capital software.")

    latest = load_table("market_risk_latest")
    unified = load_table("market_risk_results")
    comparison = load_table("model_comparison")
    stats = load_table("statistical_tests")
    stress = load_table("stress_scenarios")
    reverse = load_table("reverse_stress_solution")
    attr = load_table("attribution_volatility")
    credit_agg = load_table("credit_expected_loss")
    credit_metrics = load_table("credit_model_metrics")
    credit_stress = load_table("credit_stress")
    limits = load_table("risk_limits")
    inventory = load_table("model_inventory")
    drift = load_table("drift_metrics")
    findings = load_table("validation_findings")
    rec = load_table("sql_reconciliation")

    sql_latest = pd.DataFrame()
    try:
        repo = RiskRepository(database_url(cfg))
        repo.ensure_schema()
        sql_latest = repo.latest_risk_results(cfg["portfolio"]["id"])
    except Exception:
        pass

    st.title(page)

    if page == "Executive Overview":
        if latest.empty:
            st.warning("Run `python scripts/run_pipeline.py` first.")
            return
        max_var, max_es = latest["VaR"].max(), latest["ES"].max()
        max_stress = stress.groupby("scenario_id")["portfolio_loss"].first().max() if not stress.empty else float("nan")
        el_rate = float(credit_agg.loc[credit_agg["segment"] == "ALL", "expected_loss_rate"].iloc[0]) if not credit_agg.empty else float("nan")
        top_factor = attr.iloc[0]["risk_factor"] if not attr.empty else "N/A"
        max_util = limits["utilization"].max() if not limits.empty else float("nan")
        cols = st.columns(7)
        cols[0].metric("Portfolio notional", f"{float(cfg['portfolio'].get('notional', 0)):,.0f}")
        cols[1].metric("Max latest VaR", pct(max_var))
        cols[2].metric("Max latest ES", pct(max_es))
        cols[3].metric("Worst configured stress", pct(max_stress))
        cols[4].metric("Credit EL rate", pct(el_rate))
        cols[5].metric("Top variance driver", str(top_factor))
        cols[6].metric("Max limit utilization", pct(max_util))
        st.subheader("Latest market-risk forecasts")
        st.dataframe(latest, use_container_width=True)
        if not sql_latest.empty:
            st.caption("Latest market-risk rows below are retrieved from the SQL persistence layer.")
            st.dataframe(sql_latest, use_container_width=True)

    elif page == "Market Risk":
        if unified.empty:
            st.warning("No market-risk results available.")
            return
        unified["forecast_date"] = pd.to_datetime(unified["forecast_date"])
        model = st.selectbox("Model", sorted(unified["model"].unique()))
        g = unified[unified["model"] == model]
        c1, c2, c3 = st.columns(3)
        c1.metric("Latest VaR", pct(g.iloc[-1]["VaR"]))
        c2.metric("Latest ES", pct(g.iloc[-1]["ES"]))
        c3.metric("Exception rate", pct(g["exception"].astype(bool).mean()))
        fig = px.line(g, x="forecast_date", y=["VaR", "ES"], title=f"{model}: VaR and ES")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("VaR is a loss threshold; ES is the average loss beyond the VaR tail under the model's ES methodology.")

    elif page == "Backtesting":
        st.dataframe(comparison, use_container_width=True)
        st.dataframe(stats, use_container_width=True)
        st.info("Kupiec evaluates exception frequency. Christoffersen evaluates exception independence. Failure to reject is not proof that a model is correct.")

    elif page == "Stress Testing":
        if stress.empty:
            return
        scenario = stress.groupby("scenario_id", as_index=False)["portfolio_loss"].first().sort_values("portfolio_loss", ascending=False)
        st.plotly_chart(px.bar(scenario, x="scenario_id", y="portfolio_loss", title="Configured scenario losses"), use_container_width=True)
        st.dataframe(stress, use_container_width=True)

    elif page == "Reverse Stress":
        st.dataframe(reverse, use_container_width=True)
        if not reverse.empty:
            st.metric("Solved portfolio loss", pct(float(reverse["resulting_loss"].iloc[0])))
        st.caption("This is a minimum-norm feasible shock under the configured bounds and portfolio approximation, not the uniquely true worst-case market scenario.")

    elif page == "Risk Attribution":
        if attr.empty:
            return
        st.plotly_chart(px.bar(attr, x="risk_factor", y="pct_of_portfolio_variance", title="Variance contribution"), use_container_width=True)
        st.dataframe(attr, use_container_width=True)

    elif page == "Credit Risk":
        if credit_agg.empty:
            st.info("Credit module is disabled or has not been run.")
            return
        st.subheader("Expected Loss = PD × LGD × EAD")
        st.dataframe(credit_agg, use_container_width=True)
        st.subheader("PD model validation")
        st.dataframe(credit_metrics, use_container_width=True)
        st.subheader("Credit stress")
        st.dataframe(credit_stress, use_container_width=True)
        st.caption("Synthetic credit mode is for offline reproducibility. Do not present it as a real loan portfolio.")

    elif page == "Model Validation":
        st.subheader("Model inventory")
        st.dataframe(inventory, use_container_width=True)
        st.subheader("Input drift / PSI")
        st.dataframe(drift, use_container_width=True)
        st.subheader("Findings")
        st.dataframe(findings, use_container_width=True)
        if not rec.empty:
            st.subheader("Python ↔ SQL reconciliation")
            st.dataframe(rec, use_container_width=True)

    elif page == "Risk Limits":
        if limits.empty:
            return
        st.dataframe(limits, use_container_width=True)
        st.plotly_chart(px.bar(limits, x="metric", y="utilization", color="status", title="Limit utilization"), use_container_width=True)

    elif page == "Methodology":
        st.markdown("""
### Scope
RiskSphere is an educational, industry-style risk analytics portfolio project. It is **not** a production bank engine or regulatory capital system.

### Market risk
Historical, normal-parametric, EWMA and a transparent GARCH(1,1) challenger produce one-day out-of-sample VaR/ES forecasts. Kupiec and Christoffersen tests are reported separately.

### Rates
The 10-year rate factor is represented as an absolute yield change. When enabled, a duration/convexity approximation maps that yield shock to a bond-return proxy. DV01 is reported as a first-order sensitivity.

### Credit risk
Logistic regression is the transparent PD baseline and XGBoost is a challenger. The pipeline reports ROC-AUC, KS, Brier score and calibration. Simplified LGD/EAD baselines produce Expected Loss; credit stress changes PD and LGD assumptions.

### Governance and engineering
Data provenance, configuration-driven behavior, PSI monitoring, risk limits, a model inventory, SQL persistence/reconciliation and automated tests are included. Passing a statistical test is not proof that a model is correct.
""")


if __name__ == "__main__":
    main()
