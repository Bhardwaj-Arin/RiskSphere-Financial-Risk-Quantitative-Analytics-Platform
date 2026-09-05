"""Transparent credit feature engineering."""
from __future__ import annotations

import pandas as pd


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "loan_to_income" not in out.columns and {"loan_amount", "annual_income"}.issubset(out.columns):
        income = pd.to_numeric(out["annual_income"], errors="coerce").replace(0, pd.NA)
        out["loan_to_income"] = pd.to_numeric(out["loan_amount"], errors="coerce") / income
    if "utilization_dti_interaction" not in out.columns and {"credit_utilization", "debt_to_income"}.issubset(out.columns):
        out["utilization_dti_interaction"] = (
            pd.to_numeric(out["credit_utilization"], errors="coerce")
            * pd.to_numeric(out["debt_to_income"], errors="coerce")
        )
    return out
