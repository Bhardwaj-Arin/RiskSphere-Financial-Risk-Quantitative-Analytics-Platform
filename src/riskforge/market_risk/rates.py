"""Simple fixed-income sensitivity approximations for the rate factor."""
from __future__ import annotations

import pandas as pd


def bond_return_from_yield_change(delta_y: float, duration_years: float, convexity: float = 0.0) -> float:
    """Approximate bond return: -D*dy + 0.5*C*dy^2."""
    return float(-duration_years * delta_y + 0.5 * convexity * delta_y * delta_y)


def transform_rate_changes(changes: pd.Series, duration_years: float, convexity: float = 0.0) -> pd.Series:
    out = -duration_years * changes + 0.5 * convexity * changes.pow(2)
    out.name = changes.name
    return out


def dv01(notional: float, duration_years: float, yield_level: float | None = None) -> float:
    """First-order currency DV01. `yield_level` is accepted for API clarity;
    modified duration is supplied directly by the caller in this prototype.
    """
    _ = yield_level
    return float(notional * duration_years * 1e-4)
