"""Population Stability Index (PSI) monitoring helpers."""
from __future__ import annotations

import numpy as np
import pandas as pd


def population_stability_index(reference: pd.Series, current: pd.Series, bins: int = 10) -> float:
    ref = pd.to_numeric(reference, errors="coerce").dropna().to_numpy()
    cur = pd.to_numeric(current, errors="coerce").dropna().to_numpy()
    if len(ref) < bins or len(cur) < bins:
        return float("nan")
    edges = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return 0.0
    edges[0], edges[-1] = -np.inf, np.inf
    r_count, _ = np.histogram(ref, bins=edges)
    c_count, _ = np.histogram(cur, bins=edges)
    eps = 1e-6
    r_pct = np.maximum(r_count / max(r_count.sum(), 1), eps)
    c_pct = np.maximum(c_count / max(c_count.sum(), 1), eps)
    return float(np.sum((c_pct - r_pct) * np.log(c_pct / r_pct)))


def monitor_dataframe(reference: pd.DataFrame, current: pd.DataFrame, features: list[str] | None = None,
                      bins: int = 10, warning_threshold: float = 0.10,
                      breach_threshold: float = 0.25) -> pd.DataFrame:
    features = features or [c for c in reference.columns if c in current.columns]
    rows = []
    for col in features:
        if not pd.api.types.is_numeric_dtype(reference[col]):
            continue
        psi = population_stability_index(reference[col], current[col], bins)
        if np.isnan(psi):
            status = "INSUFFICIENT_DATA"
        elif psi >= breach_threshold:
            status = "BREACH"
        elif psi >= warning_threshold:
            status = "WARNING"
        else:
            status = "OK"
        rows.append({"feature": col, "psi": psi, "status": status})
    return pd.DataFrame(rows)
