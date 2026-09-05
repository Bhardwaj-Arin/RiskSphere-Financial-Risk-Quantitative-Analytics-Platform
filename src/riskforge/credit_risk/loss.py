"""Transparent LGD/EAD and Expected Loss calculations."""
from __future__ import annotations

import numpy as np
import pandas as pd


def add_expected_loss(predictions: pd.DataFrame, pd_column: str, ead_column: str = "ead",
                      lgd: float = 0.45) -> pd.DataFrame:
    if not 0 <= lgd <= 1:
        raise ValueError("LGD must be in [0,1]")
    out = predictions.copy()
    out["lgd"] = float(lgd)
    out["pd"] = out[pd_column].clip(0, 1)
    out["ead"] = pd.to_numeric(out[ead_column], errors="raise").clip(lower=0)
    out["expected_loss"] = out["pd"] * out["lgd"] * out["ead"]
    return out


def aggregate_expected_loss(df: pd.DataFrame, segment_column: str = "segment") -> pd.DataFrame:
    rows = [{
        "segment": "ALL",
        "ead": float(df["ead"].sum()),
        "expected_loss": float(df["expected_loss"].sum()),
        "expected_loss_rate": float(df["expected_loss"].sum() / max(df["ead"].sum(), 1e-12)),
        "mean_pd": float(df["pd"].mean()),
    }]
    if segment_column in df.columns:
        for seg, g in df.groupby(segment_column):
            rows.append({
                "segment": str(seg), "ead": float(g["ead"].sum()),
                "expected_loss": float(g["expected_loss"].sum()),
                "expected_loss_rate": float(g["expected_loss"].sum() / max(g["ead"].sum(), 1e-12)),
                "mean_pd": float(g["pd"].mean()),
            })
    return pd.DataFrame(rows)
