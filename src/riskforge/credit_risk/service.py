"""End-to-end credit-risk service."""
from __future__ import annotations

import pandas as pd
from sklearn.metrics import brier_score_loss

from riskforge.credit_risk.data import load_credit_data
from riskforge.credit_risk.models import train_pd_models
from riskforge.credit_risk.loss import add_expected_loss, aggregate_expected_loss
from riskforge.credit_risk.stress import run_credit_stress
from riskforge.credit_risk.quality import validate_credit_data, leakage_scan
from riskforge.credit_risk.features import engineer_features


def _segment_performance(losses: pd.DataFrame) -> pd.DataFrame:
    if "segment" not in losses.columns:
        return pd.DataFrame()
    rows = []
    for segment, g in losses.groupby("segment"):
        rows.append({
            "segment": str(segment), "n": len(g),
            "observed_default_rate": float(g["default_flag"].mean()),
            "mean_predicted_pd": float(g["pd"].mean()),
            "brier_score": float(brier_score_loss(g["default_flag"], g["pd"])),
            "expected_loss_rate": float(g["expected_loss"].sum() / max(g["ead"].sum(), 1e-12)),
        })
    return pd.DataFrame(rows)


def run_credit_risk(config: dict) -> dict:
    df, metadata = load_credit_data(config)
    df = engineer_features(df)
    target = config["credit"].get("target_column", "default_flag")
    ead_col = config["credit"].get("ead_column", "ead")
    quality = validate_credit_data(df, target, ead_col)
    if not quality["passed"].all():
        raise ValueError("Credit data quality checks failed")
    leakage = leakage_scan(df, target, excluded={ead_col, "source", config["credit"].get("observation_date_column", "observation_date")})
    if not leakage.empty:
        raise ValueError(f"Potential target leakage detected: {leakage.to_dict('records')}")

    run = train_pd_models(df, config)
    preferred = "xgboost_pd" if "xgboost_pd" in run.models else "logistic_pd"
    # Challenger is not declared globally superior. It is simply the configured
    # portfolio scoring view when available; model metrics remain side-by-side.
    pd_col = f"pd_{preferred}"
    losses = add_expected_loss(run.predictions, pd_col, ead_col,
                               float(config["credit"].get("lgd_baseline", 0.45)))
    aggregate = aggregate_expected_loss(losses)
    stress = run_credit_stress(losses, config["credit_stress"]["scenarios"])
    segment = _segment_performance(losses)
    return {
        "metadata": metadata, "quality": quality, "leakage": leakage,
        "predictions": losses, "metrics": run.metrics, "calibration": run.calibration,
        "segment_performance": segment, "aggregate": aggregate, "stress": stress,
        "portfolio_model": preferred,
    }
