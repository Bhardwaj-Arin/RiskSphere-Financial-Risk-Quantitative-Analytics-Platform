"""Variance/volatility and scenario risk attribution."""
from __future__ import annotations

import numpy as np
import pandas as pd


def volatility_contribution(weights: dict[str, float], cov: pd.DataFrame) -> pd.DataFrame:
    factors = list(weights.keys())
    w = pd.Series(weights)[factors]
    sigma_w = cov.loc[factors, factors].values @ w.values
    port_var = float(w.values @ sigma_w)
    if port_var <= 0:
        raise ValueError("Non-positive portfolio variance; check inputs")
    port_vol = float(np.sqrt(port_var))
    component_variance = w.values * sigma_w
    pct = component_variance / port_var
    marginal_vol = sigma_w / port_vol
    component_vol = w.values * marginal_vol
    return pd.DataFrame({
        "risk_factor": factors,
        "weight": w.values,
        "marginal_variance": sigma_w,
        "component_variance": component_variance,
        "pct_of_portfolio_variance": pct,
        "marginal_volatility": marginal_vol,
        "component_volatility": component_vol,
    }).sort_values("pct_of_portfolio_variance", ascending=False).reset_index(drop=True)


def scenario_contribution(scenario_result_df: pd.DataFrame) -> pd.DataFrame:
    ranked = scenario_result_df.copy()
    ranked["abs_contribution"] = ranked["factor_contribution"].abs()
    ranked = ranked.sort_values("abs_contribution", ascending=False)
    total_return = ranked["factor_contribution"].sum()
    ranked["pct_of_scenario_return"] = ranked["factor_contribution"] / total_return if total_return != 0 else 0.0
    cols = ["scenario_id", "risk_factor", "shock", "factor_contribution", "pct_of_scenario_return"]
    return ranked[cols]


def factor_ranking_across_scenarios(all_scenarios_df: pd.DataFrame) -> pd.DataFrame:
    g = all_scenarios_df.copy()
    g["abs_contribution"] = g["factor_contribution"].abs()
    return (g.groupby("risk_factor")["abs_contribution"].mean()
            .sort_values(ascending=False).rename("avg_abs_contribution").reset_index())
