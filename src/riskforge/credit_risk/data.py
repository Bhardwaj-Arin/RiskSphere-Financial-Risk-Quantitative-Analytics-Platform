"""Credit-risk data loaders.

Synthetic mode is deterministic and used for offline tests. A public OpenML
`credit-g` mode is provided for real public-data experimentation when internet
access is available. The project never presents synthetic results as real data.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]


def generate_synthetic_credit(n_samples: int = 4000, seed: int = 123) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2018-01-01", periods=n_samples)
    income = rng.lognormal(np.log(65000), 0.45, n_samples).clip(18000, 300000)
    dti = rng.beta(2.2, 5.0, n_samples).clip(0.01, 0.85)
    utilization = rng.beta(2.0, 3.2, n_samples).clip(0.0, 1.0)
    delinq = rng.poisson(0.35, n_samples).clip(0, 7)
    history = rng.gamma(3.0, 2.8, n_samples).clip(0.5, 30)
    loan_amount = rng.lognormal(np.log(18000), 0.65, n_samples).clip(1000, 120000)
    loan_to_income = loan_amount / income
    interest_rate = (0.055 + 0.12 * dti + 0.08 * utilization + 0.012 * delinq + rng.normal(0, 0.012, n_samples)).clip(0.03, 0.35)
    segment = np.where(loan_amount < 12000, "small", np.where(loan_amount < 35000, "medium", "large"))

    score = (
        -4.50 + 3.1 * dti + 2.4 * utilization + 0.38 * delinq
        + 1.25 * loan_to_income + 3.3 * (interest_rate - 0.08)
        - 0.045 * history + rng.normal(0, 0.35, n_samples)
    )
    pd_true = 1.0 / (1.0 + np.exp(-score))
    default = rng.binomial(1, pd_true)
    ead = loan_amount * rng.uniform(0.75, 1.05, n_samples)

    return pd.DataFrame({
        "observation_date": dates,
        "annual_income": income,
        "debt_to_income": dti,
        "credit_utilization": utilization,
        "delinquency_count": delinq,
        "credit_history_years": history,
        "loan_amount": loan_amount,
        "loan_to_income": loan_to_income,
        "interest_rate": interest_rate,
        "segment": segment,
        "ead": ead,
        "default_flag": default,
        "source": "synthetic_credit",
    })


def load_credit_csv(path: str | Path, target_column: str = "default_flag") -> pd.DataFrame:
    path = Path(path)
    df = pd.read_csv(path)
    if target_column not in df.columns:
        raise ValueError(f"Credit CSV missing target column {target_column!r}")
    if "observation_date" in df.columns:
        df["observation_date"] = pd.to_datetime(df["observation_date"])
    df["source"] = "credit_csv"
    return df


def load_openml_credit_g(seed: int = 123) -> pd.DataFrame:
    """Load the public German Credit (credit-g) dataset via OpenML.

    This requires internet access. The dataset does not provide a genuine
    observation date, so downstream code uses a reproducible random holdout and
    explicitly records that limitation rather than inventing temporal lineage.
    """
    from sklearn.datasets import fetch_openml
    bunch = fetch_openml(name="credit-g", version=1, as_frame=True)
    df = bunch.frame.copy()
    target_name = bunch.target.name if hasattr(bunch.target, "name") else "class"
    df["default_flag"] = bunch.target.astype(str).str.lower().eq("bad").astype(int)
    if target_name in df.columns and target_name != "default_flag":
        df = df.drop(columns=[target_name])
    # Existing credit amount is a transparent EAD proxy for this educational module.
    amount_col = next((c for c in df.columns if c.lower().replace("_", " ") in {"credit amount", "credit_amount"}), None)
    df["ead"] = pd.to_numeric(df[amount_col], errors="coerce") if amount_col else 1.0
    df["source"] = "openml_credit_g"
    return df.reset_index(drop=True)


def load_credit_data(config: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    ccfg = config["credit"]
    source = str(ccfg.get("source", "synthetic")).lower()
    seed = int(ccfg.get("seed", 123))
    if source == "synthetic":
        df = generate_synthetic_credit(int(ccfg.get("n_samples", 4000)), seed)
        split_type = "chronological"
    elif source == "csv":
        path = ccfg.get("csv_path")
        if not path:
            raise ValueError("credit.csv_path is required when credit.source=csv")
        p = Path(path)
        df = load_credit_csv(REPO_ROOT / p if not p.is_absolute() else p, ccfg.get("target_column", "default_flag"))
        split_type = "chronological" if ccfg.get("observation_date_column") in df.columns else "random"
    elif source == "openml_credit_g":
        df = load_openml_credit_g(seed)
        split_type = "random"
    else:
        raise ValueError(f"Unsupported credit.source={source!r}")

    target = ccfg.get("target_column", "default_flag")
    if target not in df.columns:
        raise ValueError(f"Credit dataset missing target column {target!r}")
    if not set(pd.Series(df[target]).dropna().astype(int).unique()).issubset({0, 1}):
        raise ValueError("Credit target must be binary 0/1")
    if ccfg.get("ead_column", "ead") not in df.columns:
        raise ValueError("Credit dataset must provide EAD or an EAD proxy column")
    metadata = {
        "source": source,
        "rows": len(df),
        "default_rate": float(df[target].mean()),
        "split_type": split_type,
    }
    return df, metadata
