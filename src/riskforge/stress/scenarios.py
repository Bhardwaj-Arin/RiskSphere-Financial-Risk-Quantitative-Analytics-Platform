"""Configurable stress scenarios with factor contribution calculations."""
from __future__ import annotations

import pandas as pd


def _mapped_shock(factor: str, shock: float, mapping: dict | None) -> float:
    mapping = mapping or {}
    if mapping.get("apply_rate_duration", False) and factor == mapping.get("rate_factor", "RATES_10Y"):
        from riskforge.market_risk.rates import bond_return_from_yield_change
        return bond_return_from_yield_change(
            shock,
            float(mapping.get("duration_years", 7.0)),
            float(mapping.get("convexity", 0.0)),
        )
    return float(shock)


def apply_scenario(weights: dict[str, float], shocks: dict[str, float],
                   mapping: dict | None = None) -> dict:
    missing = set(shocks) - set(weights)
    if missing:
        raise ValueError(f"Shock references risk factors not in portfolio: {missing}")
    mapped = {f: _mapped_shock(f, s, mapping) for f, s in shocks.items()}
    contributions = {f: weights[f] * mapped[f] for f in shocks}
    portfolio_return = sum(contributions.values())
    return {
        "portfolio_return": portfolio_return,
        "portfolio_loss": -portfolio_return,
        "factor_contributions": contributions,
        "mapped_shocks": mapped,
    }


def run_scenario_set(weights: dict[str, float], scenarios: list[dict],
                     mapping: dict | None = None) -> pd.DataFrame:
    rows = []
    for sc in scenarios:
        result = apply_scenario(weights, sc["shocks"], mapping=mapping)
        for factor, shock in sc["shocks"].items():
            rows.append({
                "scenario_id": sc["id"],
                "description": sc.get("description", ""),
                "risk_factor": factor,
                "shock": shock,
                "mapped_return_shock": result["mapped_shocks"][factor],
                "factor_contribution": result["factor_contributions"][factor],
                "portfolio_loss": result["portfolio_loss"],
            })
    return pd.DataFrame(rows)


def sensitivity_analysis(weights: dict[str, float], factor: str,
                         shock_range: list[float], mapping: dict | None = None) -> pd.DataFrame:
    rows = []
    for shock in shock_range:
        result = apply_scenario(weights, {factor: shock}, mapping=mapping)
        rows.append({"risk_factor": factor, "shock": shock,
                     "mapped_return_shock": result["mapped_shocks"][factor],
                     "portfolio_loss": result["portfolio_loss"]})
    return pd.DataFrame(rows)


def historical_worst_day_scenario(returns_wide: pd.DataFrame, weights: dict[str, float],
                                  mapping: dict | None = None) -> dict:
    from riskforge.portfolio.engine import portfolio_returns
    port_ret = portfolio_returns(returns_wide, weights, mapping=mapping)
    worst_date = port_ret.idxmin()
    shocks = returns_wide.loc[worst_date].to_dict()
    result = apply_scenario(weights, shocks, mapping=mapping)
    return {
        "date": worst_date,
        "shocks": shocks,
        "portfolio_loss": result["portfolio_loss"],
        "note": "Worst observed day in the dataset used for this run; do not label it a crisis without external context.",
    }
