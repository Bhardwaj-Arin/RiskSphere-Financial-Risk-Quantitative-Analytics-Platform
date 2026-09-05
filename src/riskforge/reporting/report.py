"""Reporting (Phase 11): write CSV outputs, figures, and a structured
model-validation report from pipeline results.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

RESULTS_DIR = Path(__file__).resolve().parents[3] / "results"


def save_table(df: pd.DataFrame, name: str) -> Path:
    out = RESULTS_DIR / "tables" / f"{name}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    return out


def plot_var_vs_realized(backtest_table: pd.DataFrame, model_name: str) -> Path:
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(backtest_table["forecast_date"], backtest_table["realized_loss"],
            label="Realized loss", color="steelblue", linewidth=1)
    ax.plot(backtest_table["forecast_date"], backtest_table["var"],
            label="VaR forecast", color="firebrick", linewidth=1.2)
    exc = backtest_table[backtest_table["exception_flag"]]
    ax.scatter(exc["forecast_date"], exc["realized_loss"], color="darkorange",
               zorder=5, s=18, label="Exception")
    ax.set_title(f"{model_name}: VaR forecast vs realized loss")
    ax.set_ylabel("Loss (fraction of portfolio)")
    ax.legend()
    fig.tight_layout()
    out = RESULTS_DIR / "figures" / f"backtest_{model_name}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=140)
    plt.close(fig)
    return out


def plot_model_comparison(comparison_df: pd.DataFrame) -> Path:
    fig, ax = plt.subplots(figsize=(7, 5))
    comparison_df["exception_rate"].plot(kind="bar", ax=ax, color="steelblue", label="Observed")
    ax.axhline(comparison_df["target_rate"].iloc[0], color="firebrick",
               linestyle="--", label="Target rate")
    ax.set_ylabel("Exception rate")
    ax.set_title("Model comparison: exception rate vs target")
    ax.legend()
    fig.tight_layout()
    out = RESULTS_DIR / "figures" / "model_comparison.png"
    fig.savefig(out, dpi=140)
    plt.close(fig)
    return out


def plot_stress_scenarios(stress_df: pd.DataFrame) -> Path:
    by_scenario = stress_df.groupby("scenario_id")["portfolio_loss"].first().sort_values()
    fig, ax = plt.subplots(figsize=(8, 5))
    by_scenario.plot(kind="barh", ax=ax, color="darkred")
    ax.set_xlabel("Portfolio loss")
    ax.set_title("Stress scenario losses")
    fig.tight_layout()
    out = RESULTS_DIR / "figures" / "stress_scenarios.png"
    fig.savefig(out, dpi=140)
    plt.close(fig)
    return out


def write_model_validation_report(context: dict[str, Any]) -> Path:
    """Structured report per blueprint validation-report outline:
    objective, data, assumptions, implementation, test design, results,
    failures/exceptions, limitations, conclusion, next steps.
    """
    lines = [
        "# RiskForge-QRM Model Validation Report",
        "",
        f"Generated: {dt.datetime.utcnow().isoformat()}Z",
        "",
        "**Scope statement:** Educational prototype. Not a production risk "
        "engine. Not a claim of Basel/regulatory compliance.",
        "",
        "## 1. Model objective",
        context.get("objective", ""),
        "",
        "## 2. Data",
        context.get("data_summary", ""),
        "",
        "## 3. Assumptions",
        context.get("assumptions", ""),
        "",
        "## 4. Implementation",
        context.get("implementation", ""),
        "",
        "## 5. Test design",
        context.get("test_design", ""),
        "",
        "## 6. Results",
        context.get("results_summary", ""),
        "",
        "## 7. Failures / exceptions observed",
        context.get("failures", ""),
        "",
        "## 8. Limitations",
        context.get("limitations", ""),
        "",
        "## 9. Conclusion",
        context.get("conclusion", ""),
        "",
        "## 10. Recommended next steps",
        context.get("next_steps", ""),
    ]
    out = RESULTS_DIR / "reports" / "model_validation_report.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(str(l) for l in lines))
    return out


def save_json(payload: Any, name: str, subdir: str = "reports") -> Path:
    import json
    out = RESULTS_DIR / subdir / f"{name}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return out


def write_individual_model_reports(market_stats: pd.DataFrame, market_stability: pd.DataFrame,
                                   credit_metrics: pd.DataFrame | None = None) -> list[Path]:
    """Write compact per-model validation reports with non-overclaiming language."""
    out_dir = RESULTS_DIR / "reports" / "models"
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for _, r in market_stats.iterrows():
        model_id = str(r["model_id"])
        stability = market_stability[market_stability["model_id"] == model_id]
        text = [
            f"# Validation Report — {model_id}", "",
            "## Purpose", "One-day portfolio VaR/ES model in the RiskQuant educational risk workflow.", "",
            "## Backtesting", f"Forecasts: {int(r['n_obs'])}; exceptions: {int(r['n_exceptions'])}; "
            f"Kupiec p={float(r['p_value']):.6f}; Christoffersen p={float(r['christ_p_value']):.6f}.", "",
            "## Interpretation", "A p-value above the configured threshold means the test did not reject its null; it does not prove the model is correct.", "",
            "## Stability by period", stability.to_string(index=False), "",
            "## Scope limitation", "Educational risk-factor prototype; not regulatory model approval or production validation.",
        ]
        p = out_dir / f"{model_id}.md"
        p.write_text("\n".join(text), encoding="utf-8")
        paths.append(p)
    if credit_metrics is not None and not credit_metrics.empty:
        for _, r in credit_metrics.iterrows():
            model_id = str(r["model_id"])
            text = [
                f"# Validation Report — {model_id}", "", "## Purpose",
                "Probability-of-default baseline/challenger in the educational credit-risk module.", "",
                "## Holdout metrics",
                f"ROC-AUC={float(r['roc_auc']):.6f}; KS={float(r['ks']):.6f}; Brier={float(r['brier_score']):.6f}; "
                f"mean predicted PD={float(r['mean_predicted_pd']):.4%}; observed default rate={float(r['observed_default_rate']):.4%}.", "",
                "## Split", str(r.get("split_type", "unknown")), "",
                "## Scope limitation", "Metrics are dataset-dependent and do not establish regulatory model fitness.",
            ]
            p = out_dir / f"{model_id}.md"
            p.write_text("\n".join(text), encoding="utf-8")
            paths.append(p)
    return paths
