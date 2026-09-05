import copy
import pandas as pd
import pytest

from riskforge.utils.config import load_config, validate_base_config, risk_settings
from riskforge.market_risk.results import build_unified_results, REQUIRED_COLUMNS


def test_single_canonical_training_window():
    cfg = load_config("base.yaml")
    rs = risk_settings(cfg)
    assert rs.training_window == cfg["risk"]["training_window"]
    assert "min_train_window" not in cfg["risk"]
    assert "window" not in cfg["risk"]


def test_conflicting_legacy_window_is_rejected():
    cfg = load_config("base.yaml")
    bad = copy.deepcopy(cfg)
    bad["risk"]["window"] = bad["risk"]["training_window"] + 1
    with pytest.raises(ValueError, match="Conflicting rolling-window"):
        validate_base_config(bad)


def test_unified_result_contract_contains_required_fields():
    dates = pd.bdate_range("2024-01-01", periods=4)
    realized = pd.Series([0.0, -0.03, 0.01, -0.01], index=dates)
    var = pd.Series([0.02, 0.02], index=dates[2:])
    es = pd.Series([0.03, 0.03], index=dates[2:])
    out = build_unified_results({"m": var}, {"m": es}, realized, 0.99, 1, 2, "v1")
    assert list(out.columns) == REQUIRED_COLUMNS
    assert len(out) == 2
    assert out["ES"].ge(out["VaR"]).all()
