import pandas as pd

from riskforge.data import synthetic, quality
from riskforge.portfolio.engine import portfolio_returns
from riskforge.market_risk.service import run_market_risk
from riskforge.validation.backtest import build_backtest_table
from riskforge.stress.scenarios import run_scenario_set
from riskforge.utils.config import load_config


def test_small_market_flow_integration():
    cfg = load_config("base.yaml")
    cfg["data"]["start_date"] = "2020-01-01"
    cfg["data"]["end_date"] = "2021-12-31"
    cfg["garch"]["enabled"] = True
    prices = synthetic.generate_market_prices(cfg["data"]["start_date"], cfg["data"]["end_date"], cfg["data"]["risk_factors"], seed=99)
    levels = quality.long_to_wide_levels(prices)
    moves = quality.levels_to_returns(levels)
    port = portfolio_returns(moves, cfg["portfolio"]["weights"], cfg["portfolio"]["mapping"])
    unified, _, _ = run_market_risk(port, cfg, "integration")
    assert {"historical_var", "parametric_var", "ewma_var", "garch_var"}.issubset(set(unified["model"]))
    first_model = unified["model"].iloc[0]
    s = unified[unified["model"] == first_model].set_index("forecast_date")["VaR"]
    bt = build_backtest_table(s, port, first_model)
    assert len(bt) > 0
    stress = run_scenario_set(cfg["portfolio"]["weights"], [{"id": "S", "shocks": {"EQUITY_INDEX": -0.1}}], cfg["portfolio"]["mapping"])
    assert stress["portfolio_loss"].iloc[0] > 0
