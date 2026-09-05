"""Model inventory and structured validation findings."""
from __future__ import annotations

import pandas as pd


def build_model_inventory(config: dict, credit_enabled: bool = True, garch_enabled: bool = True) -> pd.DataFrame:
    version = str(config.get("model_version", "unknown"))
    data_source = str(config["data"].get("source", "unknown"))
    market_period = f"{config['data'].get('start_date')} to {config['data'].get('end_date')}"
    rows = [
        {"model_id": "historical_var", "purpose": "Market VaR", "target": "1-day portfolio loss quantile",
         "data": data_source, "training_period": market_period, "features": "portfolio returns", "assumptions": "empirical rolling distribution",
         "limitations": "historical window may not represent future tail", "version": version, "validation_status": "VALIDATED"},
        {"model_id": "parametric_var", "purpose": "Market VaR", "target": "1-day portfolio loss quantile",
         "data": data_source, "training_period": market_period, "features": "portfolio returns", "assumptions": "conditional normality in rolling window",
         "limitations": "normal tails can understate extreme loss", "version": version, "validation_status": "VALIDATED"},
        {"model_id": "ewma_var", "purpose": "Market VaR", "target": "1-day portfolio loss quantile",
         "data": data_source, "training_period": market_period, "features": "portfolio returns", "assumptions": "EWMA volatility; normal tail",
         "limitations": "fixed decay factor; normal tail", "version": version, "validation_status": "VALIDATED"},
    ]
    if garch_enabled:
        rows.append({"model_id": "garch_var", "purpose": "Market VaR challenger", "target": "1-day portfolio loss quantile",
                     "data": data_source, "training_period": market_period, "features": "portfolio returns", "assumptions": "GARCH(1,1); Gaussian QMLE",
                     "limitations": "initial-window parameter fit; normal conditional tail", "version": version,
                     "validation_status": "CHALLENGER"})
    if credit_enabled:
        rows += [
            {"model_id": "logistic_pd", "purpose": "Credit PD baseline", "target": "default probability",
             "data": str(config["credit"].get("source", "unknown")), "training_period": "dataset split recorded in credit validation outputs", "features": "credit application/risk features",
             "assumptions": "log-odds linear after preprocessing", "limitations": "educational dataset; simplified target definition",
             "version": version, "validation_status": "VALIDATED"},
            {"model_id": "xgboost_pd", "purpose": "Credit PD challenger", "target": "default probability",
             "data": str(config["credit"].get("source", "unknown")), "training_period": "dataset split recorded in credit validation outputs", "features": "credit application/risk features",
             "assumptions": "gradient-boosted trees", "limitations": "less interpretable; educational dataset",
             "version": version, "validation_status": "CHALLENGER"},
        ]
    return pd.DataFrame(rows)


def build_findings(statistical_tests: pd.DataFrame | None,
                   drift: pd.DataFrame | None,
                   limits: pd.DataFrame | None) -> pd.DataFrame:
    rows: list[dict] = []
    if statistical_tests is not None and not statistical_tests.empty:
        for _, r in statistical_tests.iterrows():
            if not bool(r.get("overall_pass", False)):
                rows.append({
                    "finding_id": f"MARKET_BACKTEST_{r['model_id']}", "severity": "MEDIUM",
                    "evidence": f"Backtest did not pass both 5% tests; Kupiec p={r.get('p_value', float('nan')):.4g}, Christoffersen p={r.get('christ_p_value', float('nan')):.4g}",
                    "recommendation": "Review coverage and volatility assumptions; do not infer model validity from one test.",
                    "status": "OPEN",
                })
    if drift is not None and not drift.empty:
        for _, r in drift.iterrows():
            if str(r.get("status")) in {"WARNING", "BREACH"}:
                rows.append({
                    "finding_id": f"DRIFT_{r['feature']}", "severity": "HIGH" if r["status"] == "BREACH" else "LOW",
                    "evidence": f"PSI={r['psi']:.4f} ({r['status']})", "recommendation": "Investigate input distribution shift before relying on model output.",
                    "status": "OPEN",
                })
    if limits is not None and not limits.empty:
        for _, r in limits.iterrows():
            if r["status"] == "BREACH":
                rows.append({
                    "finding_id": f"LIMIT_{r['metric']}", "severity": "HIGH",
                    "evidence": f"{r['metric']} utilization={r['utilization']:.1%}",
                    "recommendation": "Escalate the risk-limit breach and review exposure/scenario assumptions.",
                    "status": "OPEN",
                })
    if not rows:
        rows.append({"finding_id": "NO_MATERIAL_FINDING", "severity": "INFO", "evidence": "No configured rule triggered in this run.",
                     "recommendation": "Continue periodic validation and monitoring.", "status": "CLOSED"})
    return pd.DataFrame(rows)
