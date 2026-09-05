import numpy as np
import pandas as pd

from riskforge.market_risk.garch import fit_garch11_qmle, rolling_garch11_forecast
from riskforge.market_risk.rates import bond_return_from_yield_change, dv01
from riskforge.governance.limits import evaluate_limits


def test_garch_parameters_are_stationary():
    rng = np.random.default_rng(9)
    r = pd.Series(rng.normal(0, 0.01, 300))
    p = fit_garch11_qmle(r)
    assert p.omega > 0
    assert p.alpha >= 0 and p.beta >= 0
    assert p.alpha + p.beta < 1


def test_garch_forecast_is_strictly_out_of_sample_for_first_date():
    rng = np.random.default_rng(10)
    idx = pd.bdate_range("2020-01-01", periods=320)
    r1 = pd.Series(rng.normal(0, 0.01, 320), index=idx)
    r2 = r1.copy()
    r2.iloc[251:] = r2.iloc[251:] * 25  # change only future observations
    f1 = rolling_garch11_forecast(r1, 0.99, 250)
    f2 = rolling_garch11_forecast(r2, 0.99, 250)
    assert abs(f1.iloc[0]["var"] - f2.iloc[0]["var"]) < 1e-12


def test_duration_dv01_sign_and_scale():
    assert bond_return_from_yield_change(0.01, duration_years=7.0) < 0
    assert abs(dv01(1_000_000, 7.0) - 700.0) < 1e-12


def test_limit_statuses():
    df = evaluate_limits({"var_99": 0.032, "stress_loss": 0.21}, {"var_99": 0.04, "stress_loss": 0.20})
    s = df.set_index("metric")["status"].to_dict()
    assert s["var_99"] == "WARNING"
    assert s["stress_loss"] == "BREACH"
