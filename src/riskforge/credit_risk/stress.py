"""Configurable credit stress scenarios with portfolio and segment impact."""
from __future__ import annotations

import pandas as pd


def _aggregate(base: pd.DataFrame, pd_stress: pd.Series, lgd_stress: pd.Series,
               scenario: dict, segment: str) -> dict:
    el = pd_stress * lgd_stress * base["ead"]
    return {
        "scenario_id": scenario["id"],
        "segment": segment,
        "pd_multiplier": float(scenario.get("pd_multiplier", 1.0)),
        "lgd_shift": float(scenario.get("lgd_shift", 0.0)),
        "mean_pd": float(pd_stress.mean()),
        "mean_lgd": float(lgd_stress.mean()),
        "total_ead": float(base["ead"].sum()),
        "expected_loss": float(el.sum()),
        "expected_loss_rate": float(el.sum() / max(base["ead"].sum(), 1e-12)),
    }


def run_credit_stress(base: pd.DataFrame, scenarios: list[dict]) -> pd.DataFrame:
    rows = []
    for sc in scenarios:
        pd_all = (base["pd"] * float(sc.get("pd_multiplier", 1.0))).clip(0, 1)
        lgd_all = (base["lgd"] + float(sc.get("lgd_shift", 0.0))).clip(0, 1)
        rows.append(_aggregate(base, pd_all, lgd_all, sc, "ALL"))
        if "segment" in base.columns:
            for segment, idx in base.groupby("segment").groups.items():
                g = base.loc[idx]
                pd_g = (g["pd"] * float(sc.get("pd_multiplier", 1.0))).clip(0, 1)
                lgd_g = (g["lgd"] + float(sc.get("lgd_shift", 0.0))).clip(0, 1)
                rows.append(_aggregate(g, pd_g, lgd_g, sc, str(segment)))
    return pd.DataFrame(rows)
