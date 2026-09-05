"""Portfolio mapping, P&L and covariance utilities."""
from __future__ import annotations

import numpy as np
import pandas as pd


def validate_weights(weights: dict[str, float], tol: float = 1e-6) -> None:
    total = sum(weights.values())
    if abs(total - 1.0) > tol:
        raise ValueError(f"Portfolio weights must sum to 1.0, got {total:.6f}")
    if any(w < -1.0 or w > 1.0 for w in weights.values()):
        raise ValueError("Weights outside [-1, 1] are unusual for this prototype; check inputs")


def map_factor_returns(returns_wide: pd.DataFrame, mapping: dict | None = None) -> pd.DataFrame:
    """Map raw risk-factor moves to asset-return proxies.

    Price factors pass through unchanged. When enabled, the configured rate
    factor (an absolute yield change) is converted using duration/convexity.
    """
    mapped = returns_wide.copy()
    mapping = mapping or {}
    if mapping.get("apply_rate_duration", False):
        from riskforge.market_risk.rates import transform_rate_changes
        factor = mapping.get("rate_factor", "RATES_10Y")
        if factor in mapped.columns:
            mapped[factor] = transform_rate_changes(
                mapped[factor],
                float(mapping.get("duration_years", 7.0)),
                float(mapping.get("convexity", 0.0)),
            )
    return mapped


def portfolio_returns(returns_wide: pd.DataFrame, weights: dict[str, float],
                      mapping: dict | None = None) -> pd.Series:
    validate_weights(weights)
    missing = set(weights) - set(returns_wide.columns)
    if missing:
        raise ValueError(f"Weights reference unknown risk factors: {missing}")
    mapped = map_factor_returns(returns_wide, mapping)
    w = pd.Series(weights)[mapped.columns.intersection(weights.keys())]
    aligned = mapped[w.index]
    port_ret = aligned.mul(w, axis=1).sum(axis=1)
    port_ret.name = "portfolio_return"
    return port_ret


def portfolio_pnl(port_returns: pd.Series, notional: float = 1_000_000.0) -> pd.Series:
    pnl = port_returns * notional
    pnl.name = "portfolio_pnl"
    return pnl


def sample_covariance(returns_wide: pd.DataFrame, mapping: dict | None = None) -> pd.DataFrame:
    return map_factor_returns(returns_wide, mapping).cov()


def portfolio_variance(weights: dict[str, float], cov: pd.DataFrame) -> float:
    w = pd.Series(weights)[cov.columns]
    return float(w.values @ cov.values @ w.values)


def manual_check_example() -> dict:
    returns = pd.DataFrame(
        {"A": [0.01, -0.02, 0.03], "B": [0.02, 0.00, -0.01]},
        index=pd.date_range("2024-01-01", periods=3),
    )
    weights = {"A": 0.6, "B": 0.4}
    expected = pd.Series([0.014, -0.012, 0.014], index=returns.index, name="portfolio_return")
    return {"returns": returns, "weights": weights, "expected": expected}
