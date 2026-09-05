from pathlib import Path
import pandas as pd

from riskforge.data import loader
from riskforge.utils.config import load_config


def test_source_dispatch_synthetic_returns_provenance():
    cfg = load_config("base.yaml")
    df, prov = loader.load_market_data(cfg)
    assert len(df) > 100
    assert prov.source == "synthetic"
    assert prov.row_count == len(df)
    assert len(prov.data_version) == 16
    assert set(prov.risk_factors) == set(cfg["data"]["risk_factors"])


def test_csv_loader_dispatch(tmp_path: Path):
    cfg = load_config("base.yaml")
    dates = pd.bdate_range("2024-01-01", periods=3)
    rows = []
    for f in cfg["data"]["risk_factors"]:
        for i, d in enumerate(dates):
            rows.append({"date": d, "risk_factor": f, "value": 100.0 + i})
    p = tmp_path / "market.csv"
    pd.DataFrame(rows).to_csv(p, index=False)
    cfg["data"]["source"] = "csv"
    cfg["data"]["csv_path"] = str(p)
    df, prov = loader.load_market_data(cfg)
    assert len(df) == 15
    assert prov.source == "csv"
