from pathlib import Path
import pandas as pd

from riskforge.database.repository import RiskRepository


def test_sql_repository_persists_and_reconciles(tmp_path: Path):
    repo = RiskRepository(f"sqlite:///{tmp_path / 'rq.db'}")
    repo.ensure_schema()
    meta = {"model_version": "test", "data_source": "synthetic", "git_commit": "none"}
    run_id = repo.start_run(meta, "dv1")
    dates = pd.bdate_range("2024-01-01", periods=2)
    risk = pd.DataFrame({
        "model": ["m", "m"], "confidence": [0.99, 0.99], "horizon": [1, 1],
        "VaR": [0.02, 0.021], "ES": [0.03, 0.031], "forecast_date": dates,
        "realized_return": [-0.01, -0.03], "exception": [False, True],
        "training_window": [250, 250], "data_version": ["dv1", "dv1"],
    })
    stress = pd.DataFrame({
        "scenario_id": ["S"], "risk_factor": ["A"], "shock": [-0.1],
        "mapped_return_shock": [-0.1], "factor_contribution": [-0.1], "portfolio_loss": [0.1],
    })
    repo.persist_risk_results(run_id, "p", risk)
    repo.persist_stress(run_id, stress)
    rec = repo.reconciliation(run_id, risk, stress)
    assert rec["passed"].all()
    repo.finish_run(run_id)
