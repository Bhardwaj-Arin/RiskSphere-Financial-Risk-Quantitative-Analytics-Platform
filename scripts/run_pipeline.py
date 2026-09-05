"""RiskSphere end-to-end pipeline.

Run from repository root:
    python scripts/run_pipeline.py

The default configuration is fully offline/reproducible for market and credit
risk. Set data.source=yfinance or csv for a real-data market workflow. Set
RISKQUANT_DATABASE_URL to a PostgreSQL SQLAlchemy URL for PostgreSQL; otherwise
an offline SQLite demonstration database is used.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

import pandas as pd

from riskforge.utils.config import load_config, risk_settings
from riskforge.utils.reproducibility import run_metadata
from riskforge.utils.logging import configure_logging
from riskforge.data import loader, quality
from riskforge.portfolio import engine as portfolio_engine
from riskforge.market_risk.service import run_market_risk
from riskforge.validation import backtest, statistical_tests
from riskforge.validation.drift import monitor_dataframe, population_stability_index
from riskforge.validation.stability import market_backtest_stability
from riskforge.stress import scenarios as stress_scenarios
from riskforge.stress import reverse_stress
from riskforge.attribution import attribution
from riskforge.credit_risk.service import run_credit_risk
from riskforge.governance.limits import evaluate_limits
from riskforge.governance.inventory import build_model_inventory, build_findings
from riskforge.database import RiskRepository, database_url
from riskforge.reporting import report


def _backtest_market(unified: pd.DataFrame, port_returns: pd.Series, confidence: float):
    backtest_tables: dict[str, pd.DataFrame] = {}
    stat_results: list[dict] = []
    for model, g in unified.groupby("model"):
        s = g.set_index("forecast_date")["VaR"].rename(model)
        table = backtest.build_backtest_table(s, port_returns, model)
        backtest_tables[model] = table
        report.save_table(table, f"backtest_{model}")
        report.plot_var_vs_realized(table, model)
        n_exc, n_obs = int(table["exception_flag"].sum()), len(table)
        kupiec = statistical_tests.kupiec_pof_test(n_exc, n_obs, 1 - confidence)
        christ = statistical_tests.christoffersen_independence_test(table["exception_flag"].values)
        cc = statistical_tests.conditional_coverage_summary(kupiec, christ)
        stat_results.append({
            "model_id": model,
            **kupiec,
            **{f"christ_{k}": v for k, v in christ.items()},
            **cc,
        })
        print(f"  {model}: exceptions={n_exc}/{n_obs} ({n_exc/n_obs:.3%}), "
              f"Kupiec p={kupiec['p_value']:.4f}, Christoffersen p={christ['p_value']:.4f}, pass={cc['overall_pass']}")
    comparison = backtest.compare_models(backtest_tables, confidence)
    report.save_table(comparison.reset_index(), "model_comparison")
    stat_df = pd.DataFrame(stat_results)
    report.save_table(stat_df, "statistical_tests")
    report.plot_model_comparison(comparison)
    return backtest_tables, comparison, stat_df


def main() -> dict:
    logger = configure_logging()
    logger.info("pipeline_start", extra={"event": "pipeline_start"})
    print("=" * 72)
    print("RiskSphere — FINANCIAL RISK & QUANTITATIVE ANALYTICS PLATFORM")
    print("=" * 72)

    config = load_config("base.yaml")
    stress_config = load_config("stress_scenarios.yaml")
    rs = risk_settings(config)
    meta = run_metadata(config)
    report.save_json(meta, "run_metadata")
    print("Run metadata:", meta)

    # Phase 2 — source-driven market data and provenance
    print("\n[Data] Loading market data and provenance...")
    prices_long, provenance = loader.load_market_data(config)
    raw_path = loader.save_raw(prices_long)
    loader.save_provenance(provenance, raw_path)
    levels_wide = quality.long_to_wide_levels(prices_long)
    returns_wide = quality.levels_to_returns(levels_wide)
    qc_report = quality.run_quality_checks(prices_long, returns_wide)
    print(qc_report.summary())
    report.save_table(qc_report.outlier_returns, "data_quality_outlier_returns")
    if not qc_report.passed:
        raise RuntimeError("Critical market-data quality checks failed; stopping before modelling")

    # Portfolio mapping incl. rates duration/DV01 proxy
    print("\n[Portfolio] Building explicit factor mapping...")
    weights = config["portfolio"]["weights"]
    mapping = config["portfolio"].get("mapping", {})
    portfolio_engine.validate_weights(weights)
    mapped_returns = portfolio_engine.map_factor_returns(returns_wide, mapping)
    port_returns = portfolio_engine.portfolio_returns(returns_wide, weights, mapping)
    print(f"Portfolio returns: {len(port_returns)} obs, mean={port_returns.mean():.6f}, std={port_returns.std():.6f}")
    if mapping.get("apply_rate_duration", False):
        from riskforge.market_risk.rates import dv01
        dv = dv01(float(config["portfolio"].get("notional", 1_000_000)), float(mapping.get("duration_years", 7.0)))
        print(f"Rate mapping active: duration={mapping.get('duration_years')}y, DV01≈{dv:,.2f} base-currency units")

    # Phases 1/3 — VaR, ES, GARCH challenger
    print("\n[Market Risk] VaR / ES / volatility challenger...")
    unified, var_series, diagnostics = run_market_risk(port_returns, config, provenance.data_version)
    report.save_table(unified, "market_risk_results")
    latest = unified.sort_values("forecast_date").groupby("model").tail(1).sort_values("model")
    report.save_table(latest, "market_risk_latest")
    print(latest[["model", "VaR", "ES", "exception"]].to_string(index=False))
    if diagnostics.get("garch_params"):
        report.save_json(diagnostics["garch_params"], "garch_parameters")
        vol = diagnostics.get("garch_volatility")
        if vol is not None:
            report.save_table(vol.rename("volatility").reset_index(), "garch_volatility")

    # Backtesting and validation
    print("\n[Validation] Out-of-sample backtesting...")
    backtest_tables, comparison, stat_df = _backtest_market(unified, port_returns, rs.confidence)
    stability_df = market_backtest_stability(backtest_tables)
    report.save_table(stability_df, "market_model_stability")

    # Stress and reverse stress
    print("\n[Stress] Configured market scenarios...")
    scenario_results = stress_scenarios.run_scenario_set(weights, stress_config["scenarios"], mapping=mapping)
    report.save_table(scenario_results, "stress_scenarios")
    report.plot_stress_scenarios(scenario_results)
    worst_day = stress_scenarios.historical_worst_day_scenario(returns_wide, weights, mapping=mapping)
    print(f"Historical sample worst day: {pd.Timestamp(worst_day['date']).date()}, loss={worst_day['portfolio_loss']:.2%}")
    sens = stress_scenarios.sensitivity_analysis(weights, "EQUITY_INDEX", [-0.30, -0.20, -0.10, 0.0, 0.10], mapping=mapping)
    report.save_table(sens, "sensitivity_equity")

    print("\n[Reverse Stress] Solving minimum-norm scenario...")
    bounds = {k: tuple(v) for k, v in config["stress"]["bounds"].items()}
    rs_result = reverse_stress.solve_reverse_stress(weights, float(config["stress"]["target_loss"]), bounds, mapping=mapping)
    verification = reverse_stress.verify_solution(weights, rs_result["shock_vector"], bounds,
                                                   float(config["stress"]["target_loss"]), mapping=mapping)
    multi_start = reverse_stress.multi_start_check(weights, float(config["stress"]["target_loss"]), bounds,
                                                   mapping=mapping)
    report.save_table(multi_start, "reverse_stress_multi_start")
    rs_row = pd.DataFrame([{
        "risk_factor": f, "shock": v, "resulting_loss": rs_result["resulting_loss"],
        "target_loss": rs_result["target_loss"], "constraint_status": rs_result["constraint_status"],
    } for f, v in rs_result["shock_vector"].items()])
    report.save_table(rs_row, "reverse_stress_solution")
    print(f"Target={rs_result['target_loss']:.1%}, resulting={rs_result['resulting_loss']:.2%}, verified={verification['verified']}")

    # Attribution
    print("\n[Attribution] Variance/component/marginal contributions...")
    cov = portfolio_engine.sample_covariance(returns_wide, mapping=mapping)
    vol_contrib = attribution.volatility_contribution(weights, cov)
    report.save_table(vol_contrib, "attribution_volatility")
    scenario_rank = attribution.factor_ranking_across_scenarios(scenario_results)
    report.save_table(scenario_rank, "attribution_scenario_ranking")
    print(vol_contrib[["risk_factor", "weight", "pct_of_portfolio_variance"]].to_string(index=False))

    # Credit risk
    credit = None
    if config.get("credit", {}).get("enabled", False):
        print("\n[Credit Risk] PD / LGD / EAD / Expected Loss...")
        credit = run_credit_risk(config)
        report.save_table(credit["quality"], "credit_data_quality")
        report.save_table(credit["leakage"], "credit_leakage_scan")
        report.save_table(credit["predictions"], "credit_predictions")
        report.save_table(credit["metrics"], "credit_model_metrics")
        report.save_table(credit["calibration"], "credit_calibration")
        report.save_table(credit["segment_performance"], "credit_segment_performance")
        report.save_table(credit["aggregate"], "credit_expected_loss")
        report.save_table(credit["stress"], "credit_stress")
        print(credit["metrics"].to_string(index=False))
        print(credit["aggregate"].to_string(index=False))

    # Monitoring / drift
    print("\n[Monitoring] Distribution stability...")
    split = max(int(len(mapped_returns) * 0.60), 1)
    recent_start = max(int(len(mapped_returns) * 0.80), split + 1)
    mcfg = config.get("monitoring", {})
    drift_df = monitor_dataframe(
        mapped_returns.iloc[:split], mapped_returns.iloc[recent_start:],
        bins=int(mcfg.get("psi_bins", 10)),
        warning_threshold=float(mcfg.get("warning_threshold", 0.10)),
        breach_threshold=float(mcfg.get("breach_threshold", 0.25)),
    )
    if credit is not None and len(credit["predictions"]) >= 40:
        pds = credit["predictions"]["pd"].reset_index(drop=True)
        half = len(pds) // 2
        psi = population_stability_index(pds.iloc[:half], pds.iloc[half:], int(mcfg.get("psi_bins", 10)))
        status = "BREACH" if psi >= float(mcfg.get("breach_threshold", 0.25)) else ("WARNING" if psi >= float(mcfg.get("warning_threshold", 0.10)) else "OK")
        drift_df = pd.concat([drift_df, pd.DataFrame([{"feature": "credit_pd_distribution", "psi": psi, "status": status}])], ignore_index=True)
    report.save_table(drift_df, "drift_metrics")
    print(drift_df.to_string(index=False))

    # Limits and governance
    latest_max_var = float(latest["VaR"].max())
    latest_max_es = float(latest["ES"].max())
    max_stress = float(scenario_results.groupby("scenario_id")["portfolio_loss"].first().max())
    credit_el_rate = 0.0
    if credit is not None:
        credit_el_rate = float(credit["aggregate"].loc[credit["aggregate"]["segment"] == "ALL", "expected_loss_rate"].iloc[0])
    risk_metrics = {"var_99": latest_max_var, "es_99": latest_max_es,
                    "stress_loss": max_stress, "credit_expected_loss": credit_el_rate}
    limits_df = evaluate_limits(risk_metrics, config.get("limits", {}))
    report.save_table(limits_df, "risk_limits")

    inventory_df = build_model_inventory(config, credit_enabled=credit is not None,
                                         garch_enabled=config.get("garch", {}).get("enabled", False))
    findings_df = build_findings(stat_df, drift_df, limits_df)
    report.save_table(inventory_df, "model_inventory")
    report.save_table(findings_df, "validation_findings")

    # SQL persistence + reconciliation
    db_status: dict = {"enabled": False}
    reconciliation_df = pd.DataFrame()
    if config.get("database", {}).get("enabled", False):
        print("\n[SQL] Persisting generated results...")
        repo = RiskRepository(database_url(config))
        repo.ensure_schema()
        run_id = repo.start_run(meta, provenance.data_version)
        try:
            repo.persist_market_prices(run_id, prices_long)
            repo.persist_positions(run_id, config["portfolio"]["id"], weights, float(config["portfolio"].get("notional", 1_000_000)))
            repo.persist_risk_results(run_id, config["portfolio"]["id"], unified)
            repo.persist_backtests(run_id, backtest_tables)
            repo.persist_stress(run_id, scenario_results)
            repo.persist_attribution(run_id, vol_contrib)
            if credit is not None:
                repo.persist_credit(run_id, credit["predictions"], credit["portfolio_model"])
            repo.persist_limits(run_id, limits_df)
            repo.persist_inventory(run_id, inventory_df)
            reconciliation_df = repo.reconciliation(run_id, unified, scenario_results)
            report.save_table(reconciliation_df, "sql_reconciliation")
            if not reconciliation_df["passed"].all():
                raise RuntimeError("Python-vs-SQL reconciliation failed")
            repo.finish_run(run_id, "COMPLETED")
            db_status = {"enabled": True, "backend": repo.backend, "run_id": run_id,
                         "url_mode": "environment" if __import__("os").getenv("RISKQUANT_DATABASE_URL") else "offline_fallback"}
            print(f"SQL backend={repo.backend}, run_id={run_id}; reconciliation PASS")
        except Exception:
            repo.finish_run(run_id, "FAILED")
            raise

    # Validation report
    failures = []
    for _, row in stat_df.iterrows():
        if not bool(row["overall_pass"]):
            failures.append(f"{row['model_id']}: backtest rule did not pass (Kupiec p={row['p_value']:.4g}, Christoffersen p={row['christ_p_value']:.4g}).")
    report.write_individual_model_reports(stat_df, stability_df, None if credit is None else credit["metrics"])
    report.write_model_validation_report({
        "objective": "Estimate and validate market risk, quantify stress/reverse-stress losses, attribute risk, and extend the educational workflow into credit expected loss and monitoring.",
        "data_summary": f"Market source={provenance.source}, version={provenance.data_version}, rows={provenance.row_count}. Credit source={credit['metadata']['source'] if credit else 'disabled'}.",
        "assumptions": f"{rs.confidence:.0%} one-day VaR; {rs.training_window}-observation training window; explicit rate duration mapping; linear factor portfolio approximation; simplified credit LGD/EAD.",
        "implementation": "Historical, parametric, EWMA and GARCH challenger VaR/ES; Kupiec/Christoffersen; stress/reverse stress; attribution; credit PD baseline/challenger; SQL persistence; limits and PSI monitoring.",
        "test_design": "Strict out-of-sample market forecasts plus statistical coverage/independence tests. Credit holdout is chronological where dates exist. SQL results are reconciled to Python in-memory totals.",
        "results_summary": comparison.reset_index().to_string(index=False) + "\n\nLimits:\n" + limits_df.to_string(index=False),
        "failures": "\n".join(failures) if failures else "No configured market backtest rule failed in this run.",
        "limitations": "Educational risk-factor prototype; simplified portfolio mapping and fixed-income approximation; synthetic default datasets in offline mode; GARCH uses Gaussian QMLE; credit target/LGD/EAD are simplified and data-dependent.",
        "conclusion": "Results must be interpreted model-by-model. Passing a test does not prove a model is correct; failing a test identifies an assumption/performance issue requiring review.",
        "next_steps": "Use sourced real market/credit data, review model assumptions, run PostgreSQL deployment mode, and document dataset-specific limitations.",
    })

    summary = {
        "project": config["project"]["title"],
        "data": {"source": provenance.source, "data_version": provenance.data_version, "rows": provenance.row_count},
        "market_latest": latest[["model", "VaR", "ES", "exception"]].to_dict("records"),
        "backtesting": comparison.reset_index().to_dict("records"),
        "reverse_stress": {"resulting_loss": rs_result["resulting_loss"], "verified": verification["verified"]},
        "credit": None if credit is None else {"source": credit["metadata"]["source"], "portfolio_model": credit["portfolio_model"],
                   "expected_loss_rate": credit_el_rate},
        "limits": limits_df.to_dict("records"),
        "database": db_status,
        "reconciliation_pass": bool(reconciliation_df["passed"].all()) if not reconciliation_df.empty else None,
    }
    report.save_json(summary, "pipeline_summary")
    logger.info("pipeline_completed", extra={"event": "pipeline_completed"})
    print("\n" + "=" * 72)
    print("PIPELINE COMPLETED")
    print("=" * 72)
    return summary


if __name__ == "__main__":
    main()
