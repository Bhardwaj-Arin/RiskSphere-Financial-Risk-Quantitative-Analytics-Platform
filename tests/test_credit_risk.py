from riskforge.credit_risk.data import generate_synthetic_credit
from riskforge.credit_risk.models import train_pd_models
from riskforge.credit_risk.loss import add_expected_loss, aggregate_expected_loss
from riskforge.credit_risk.stress import run_credit_stress
from riskforge.utils.config import load_config


def test_synthetic_credit_is_reproducible_and_binary():
    a = generate_synthetic_credit(500, seed=3)
    b = generate_synthetic_credit(500, seed=3)
    assert a.equals(b)
    assert set(a["default_flag"].unique()).issubset({0, 1})
    assert 0 < a["default_flag"].mean() < 0.5


def test_credit_models_and_expected_loss_work():
    cfg = load_config("base.yaml")
    cfg["credit"]["n_samples"] = 800
    df = generate_synthetic_credit(800, seed=cfg["credit"]["seed"])
    run = train_pd_models(df, cfg)
    assert "logistic_pd" in set(run.metrics["model_id"])
    assert run.metrics["roc_auc"].between(0, 1).all()
    preferred = "xgboost_pd" if "pd_xgboost_pd" in run.predictions.columns else "logistic_pd"
    out = add_expected_loss(run.predictions, f"pd_{preferred}", "ead", 0.45)
    assert (out["expected_loss"] >= 0).all()
    agg = aggregate_expected_loss(out)
    assert "ALL" in set(agg["segment"])
    stress = run_credit_stress(out, [{"id": "B", "pd_multiplier": 1.0, "lgd_shift": 0.0},
                                     {"id": "S", "pd_multiplier": 1.5, "lgd_shift": 0.1}])
    all_rows = stress[stress["segment"] == "ALL"].set_index("scenario_id")
    assert all_rows.loc["S", "expected_loss"] >= all_rows.loc["B", "expected_loss"]
    assert set(stress["segment"]) >= {"ALL", "small", "medium", "large"}
