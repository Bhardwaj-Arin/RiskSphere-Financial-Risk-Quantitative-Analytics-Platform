"""Expected Shortfall estimators and out-of-sample forecast helpers."""
from __future__ import annotations

import pandas as pd
from scipy import stats


def historical_es(returns: pd.Series, confidence: float = 0.99) -> float:
    q = returns.quantile(1 - confidence)
    tail = returns[returns <= q]
    return float(-q if tail.empty else -tail.mean())


def parametric_es(returns: pd.Series, confidence: float = 0.99) -> float:
    mu = returns.mean()
    sigma = returns.std(ddof=1)
    z = stats.norm.ppf(1 - confidence)
    return float(-mu + sigma * stats.norm.pdf(z) / (1 - confidence))


def normal_es_from_moments(mu: float, sigma: float, confidence: float = 0.99) -> float:
    z = stats.norm.ppf(1 - confidence)
    return float(-mu + sigma * stats.norm.pdf(z) / (1 - confidence))


def rolling_historical_es(returns: pd.Series, confidence: float = 0.99,
                          window: int = 250) -> pd.Series:
    if len(returns) <= window:
        raise ValueError(f"Need more than {window} observations, got {len(returns)}")
    forecasts = {
        returns.index[t]: historical_es(returns.iloc[t-window:t], confidence)
        for t in range(window, len(returns))
    }
    result = pd.Series(forecasts, name="historical_es")
    result.index.name = "date"
    return result


def rolling_parametric_es(returns: pd.Series, confidence: float = 0.99,
                          window: int = 250) -> pd.Series:
    if len(returns) <= window:
        raise ValueError(f"Need more than {window} observations, got {len(returns)}")
    forecasts = {
        returns.index[t]: parametric_es(returns.iloc[t-window:t], confidence)
        for t in range(window, len(returns))
    }
    result = pd.Series(forecasts, name="parametric_es")
    result.index.name = "date"
    return result
