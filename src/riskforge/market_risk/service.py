"""Market-risk service combining existing VaR models with standardized ES."""
from __future__ import annotations

import pandas as pd

from riskforge.models import historical_var, parametric_var, ewma, expected_shortfall
from riskforge.market_risk import garch
from riskforge.market_risk.results import build_unified_results


def run_market_risk(port_returns: pd.Series, config: dict, data_version: str) -> tuple[pd.DataFrame, dict[str, pd.Series], dict]:
    rcfg = config["risk"]
    confidence = float(rcfg["confidence"])
    window = int(rcfg["training_window"])
    horizon = int(rcfg.get("horizon_days", 1))

    hvar = historical_var.rolling_historical_var(port_returns, confidence, window)
    pvar = parametric_var.rolling_parametric_var(port_returns, confidence, window)
    evar = ewma.rolling_ewma_var_forecast(port_returns, confidence, float(config["ewma"]["lambda"]), window)
    hes = expected_shortfall.rolling_historical_es(port_returns, confidence, window)
    pes = expected_shortfall.rolling_parametric_es(port_returns, confidence, window)

    # EWMA ES uses the same conditional-normal approximation as EWMA VaR.
    from scipy import stats
    e_es = {}
    z = stats.norm.ppf(1 - confidence)
    tail_mult = stats.norm.pdf(z) / (1 - confidence)
    for dt in evar.index:
        t = port_returns.index.get_loc(dt)
        hist = port_returns.iloc[:t]
        vol_path = ewma.ewma_volatility(hist, lam=float(config["ewma"]["lambda"]), seed_window=min(30, len(hist)-1))
        sigma_t = float(vol_path.iloc[-1])
        mu_t = float(hist.iloc[-window:].mean())
        e_es[dt] = float(-mu_t + sigma_t * tail_mult)
    ees = pd.Series(e_es, name="ewma_es")

    vars_: dict[str, pd.Series] = {
        "historical_var": hvar,
        "parametric_var": pvar,
        "ewma_var": evar,
    }
    ess: dict[str, pd.Series] = {
        "historical_var": hes,
        "parametric_var": pes,
        "ewma_var": ees,
    }
    diagnostics: dict = {}

    if config.get("garch", {}).get("enabled", False):
        gdf = garch.rolling_garch11_forecast(port_returns, confidence, window)
        vars_["garch_var"] = gdf["var"].rename("garch_var")
        ess["garch_var"] = gdf["es"].rename("garch_es")
        diagnostics["garch_params"] = gdf.attrs.get("garch_params", {})
        diagnostics["garch_volatility"] = gdf["volatility"]

    unified = build_unified_results(
        vars_, ess, port_returns, confidence, horizon, window, data_version
    )
    return unified, vars_, diagnostics
