"""Small, transparent GARCH(1,1) challenger implemented with SciPy.

The challenger is intentionally simple: parameters are estimated on the
initial training window using Gaussian quasi-maximum likelihood and then
conditional variance is updated out-of-sample using only information that has
already arrived. This avoids look-ahead and avoids adding a large dependency.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy import optimize, stats

from riskforge.models.expected_shortfall import normal_es_from_moments


@dataclass(frozen=True)
class GarchParams:
    omega: float
    alpha: float
    beta: float


def _variance_path(x: np.ndarray, params: GarchParams, seed_var: float) -> np.ndarray:
    var = np.empty(len(x), dtype=float)
    var[0] = max(seed_var, 1e-12)
    for t in range(1, len(x)):
        var[t] = params.omega + params.alpha * x[t-1] ** 2 + params.beta * var[t-1]
        var[t] = max(var[t], 1e-12)
    return var


def fit_garch11_qmle(returns: pd.Series) -> GarchParams:
    if len(returns) < 50:
        raise ValueError("GARCH fitting requires at least 50 observations")
    x = returns.astype(float).to_numpy()
    x = x - x.mean()
    scale = 100.0
    y = x * scale
    seed_var = float(np.var(y, ddof=1))

    def nll(theta: np.ndarray) -> float:
        omega, alpha, beta = theta
        if omega <= 0 or alpha < 0 or beta < 0 or alpha + beta >= 0.999:
            return 1e30
        p = GarchParams(float(omega), float(alpha), float(beta))
        v = _variance_path(y, p, seed_var)
        return float(0.5 * np.sum(np.log(2 * np.pi) + np.log(v) + (y ** 2) / v))

    x0 = np.array([max(seed_var * 0.02, 1e-6), 0.06, 0.92])
    bounds = [(1e-10, max(seed_var * 10, 1e-4)), (1e-6, 0.5), (1e-6, 0.998)]
    constraints = ({"type": "ineq", "fun": lambda th: 0.999 - th[1] - th[2]},)
    res = optimize.minimize(nll, x0, method="SLSQP", bounds=bounds, constraints=constraints,
                            options={"maxiter": 400, "ftol": 1e-9})
    if not res.success:
        # Conservative stable fallback, scaled to the initial unconditional variance.
        alpha, beta = 0.06, 0.92
        omega = max(seed_var * (1 - alpha - beta), 1e-10)
    else:
        omega, alpha, beta = map(float, res.x)
    # Convert omega from percent-return variance back to raw-return variance.
    return GarchParams(omega=omega / (scale ** 2), alpha=alpha, beta=beta)


def rolling_garch11_forecast(returns: pd.Series, confidence: float = 0.99,
                             training_window: int = 250) -> pd.DataFrame:
    """One-step-ahead out-of-sample GARCH VaR/ES forecasts.

    Parameters are fitted on the initial training window. The variance state is
    then updated recursively. No observation at date t enters the forecast for t.
    """
    if len(returns) <= training_window:
        raise ValueError(f"Need more than {training_window} observations, got {len(returns)}")
    params = fit_garch11_qmle(returns.iloc[:training_window])
    initial = returns.iloc[:training_window]
    mu0 = float(initial.mean())
    residuals = (initial - mu0).to_numpy()
    seed_var = float(np.var(residuals, ddof=1))
    var_path = _variance_path(residuals, params, seed_var)
    # variance forecast for first OOS date based on last training residual.
    current_var = params.omega + params.alpha * residuals[-1] ** 2 + params.beta * var_path[-1]
    z = stats.norm.ppf(1 - confidence)
    rows = []
    for t in range(training_window, len(returns)):
        hist = returns.iloc[max(0, t-training_window):t]
        mu_t = float(hist.mean())
        sigma_t = float(np.sqrt(max(current_var, 1e-12)))
        var_t = float(-(mu_t + z * sigma_t))
        es_t = normal_es_from_moments(mu_t, sigma_t, confidence)
        rows.append((returns.index[t], var_t, es_t, sigma_t))
        # Update state only after the date-t return has been realized.
        resid_t = float(returns.iloc[t] - mu_t)
        current_var = params.omega + params.alpha * resid_t ** 2 + params.beta * current_var
    out = pd.DataFrame(rows, columns=["forecast_date", "var", "es", "volatility"]).set_index("forecast_date")
    out.attrs["garch_params"] = {"omega": params.omega, "alpha": params.alpha, "beta": params.beta}
    return out
