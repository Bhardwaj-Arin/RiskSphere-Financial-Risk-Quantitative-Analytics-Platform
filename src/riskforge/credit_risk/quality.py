"""Credit data quality and simple leakage guards."""
from __future__ import annotations

import numpy as np
import pandas as pd


def validate_credit_data(df: pd.DataFrame, target: str, ead_column: str) -> pd.DataFrame:
    checks = []
    checks.append({"check": "target_present", "passed": target in df.columns, "detail": target})
    checks.append({"check": "ead_present", "passed": ead_column in df.columns, "detail": ead_column})
    if target in df.columns:
        target_ok = set(pd.Series(df[target]).dropna().astype(int).unique()).issubset({0, 1})
        checks.append({"check": "binary_target", "passed": bool(target_ok), "detail": "target must be 0/1"})
        checks.append({"check": "target_missing", "passed": bool(df[target].isna().sum() == 0),
                       "detail": f"missing={int(df[target].isna().sum())}"})
    if ead_column in df.columns:
        ead = pd.to_numeric(df[ead_column], errors="coerce")
        checks.append({"check": "ead_nonnegative", "passed": bool((ead.dropna() >= 0).all()),
                       "detail": f"missing_or_non_numeric={int(ead.isna().sum())}"})
    return pd.DataFrame(checks)


def leakage_scan(df: pd.DataFrame, target: str, excluded: set[str] | None = None) -> pd.DataFrame:
    """Flag obvious leakage candidates; this is a guardrail, not proof of no leakage."""
    excluded = excluded or set()
    y = pd.to_numeric(df[target], errors="coerce")
    rows = []
    for col in df.columns:
        if col == target or col in excluded:
            continue
        name_flag = any(tok in col.lower() for tok in ["default_flag", "target", "outcome", "post_default"])
        corr = np.nan
        if pd.api.types.is_numeric_dtype(df[col]):
            x = pd.to_numeric(df[col], errors="coerce")
            if x.nunique(dropna=True) > 1 and y.nunique(dropna=True) > 1:
                corr = float(x.corr(y))
        corr_flag = bool(not np.isnan(corr) and abs(corr) > 0.995)
        if name_flag or corr_flag:
            rows.append({"feature": col, "reason": "suspicious_name" if name_flag else "near_perfect_target_correlation",
                         "correlation_with_target": corr})
    return pd.DataFrame(rows, columns=["feature", "reason", "correlation_with_target"])
