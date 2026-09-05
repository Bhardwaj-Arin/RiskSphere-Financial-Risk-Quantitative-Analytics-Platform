"""Standardized market-risk forecast result contract."""
from __future__ import annotations

from typing import Mapping
import pandas as pd

REQUIRED_COLUMNS = [
    "model", "confidence", "horizon", "VaR", "ES", "forecast_date",
    "realized_return", "exception", "training_window", "data_version",
]


def build_unified_results(
    var_forecasts: Mapping[str, pd.Series],
    es_forecasts: Mapping[str, pd.Series],
    realized_returns: pd.Series,
    confidence: float,
    horizon: int,
    training_window: int,
    data_version: str,
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for model, var_series in var_forecasts.items():
        if model not in es_forecasts:
            raise ValueError(f"No ES forecast supplied for model {model}")
        es_series = es_forecasts[model].reindex(var_series.index)
        realized = realized_returns.reindex(var_series.index)
        frame = pd.DataFrame({
            "model": model,
            "confidence": confidence,
            "horizon": horizon,
            "VaR": var_series.astype(float),
            "ES": es_series.astype(float),
            "forecast_date": var_series.index,
            "realized_return": realized.astype(float),
            "training_window": training_window,
            "data_version": data_version,
        })
        frame["exception"] = (-frame["realized_return"]) > frame["VaR"]
        frames.append(frame[REQUIRED_COLUMNS])
    result = pd.concat(frames, ignore_index=True)
    result["forecast_date"] = pd.to_datetime(result["forecast_date"])
    return result.sort_values(["model", "forecast_date"]).reset_index(drop=True)


def latest_by_model(results: pd.DataFrame) -> pd.DataFrame:
    idx = results.groupby("model")["forecast_date"].idxmax()
    return results.loc[idx].sort_values("model").reset_index(drop=True)
