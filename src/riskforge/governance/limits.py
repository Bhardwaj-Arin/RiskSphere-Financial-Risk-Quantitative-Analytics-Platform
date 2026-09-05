"""Risk-limit evaluation and utilization/breach status."""
from __future__ import annotations

import math
import pandas as pd


def _status(utilization: float) -> str:
    if utilization > 1.0:
        return "BREACH"
    if utilization >= 0.80:
        return "WARNING"
    return "OK"


def evaluate_limits(metrics: dict[str, float], limits: dict[str, float]) -> pd.DataFrame:
    rows = []
    for metric, value in metrics.items():
        if metric not in limits:
            continue
        limit = float(limits[metric])
        utilization = float(value / limit) if limit > 0 else math.inf
        rows.append({
            "metric": metric,
            "value": float(value),
            "limit": limit,
            "utilization": utilization,
            "status": _status(utilization),
        })
    return pd.DataFrame(rows)
