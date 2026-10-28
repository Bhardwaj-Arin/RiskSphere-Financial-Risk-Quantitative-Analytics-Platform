"""RiskSphere - a story-driven Streamlit dashboard.

Goal: anyone opening this app for the first time should understand
  (1) what was built, (2) which methods/tools were used, (3) what the results are,
in plain English, with interactive charts instead of bare tables.

Run from the repository root:   streamlit run dashboard/app.py
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import plotly.graph_objects as go
import streamlit as st

RESULTS = ROOT / "results" / "tables"
REPORTS = ROOT / "results" / "reports"
GITHUB = "https://github.com/Bhardwaj-Arin/RiskSphere-Financial-Risk-Quantitative-Analytics-Platform"
LIVE = "https://risksphere-financial-risk-quantitative-analytics-platform-ku22.streamlit.app/"

# ----------------------------------------------------------------------------
# Look & feel
# ----------------------------------------------------------------------------
INDIGO, TEAL, AMBER, RED = "#6366F1", "#14B8A6", "#F59E0B", "#EF4444"
GREEN, PINK, SKY, SLATE = "#22C55E", "#EC4899", "#38BDF8", "#94A3B8"

MODEL_LABEL = {
    "historical_var": "Historical", "parametric_var": "Parametric (Normal)",
    "ewma_var": "EWMA", "garch_var": "GARCH(1,1)",
    "logistic_pd": "Logistic Regression", "xgboost_pd": "XGBoost",
}
MODEL_COLOR = {
    "historical_var": AMBER, "parametric_var": SKY, "ewma_var": PINK,
    "garch_var": TEAL, "logistic_pd": INDIGO, "xgboost_pd": TEAL,
}
FACTOR_LABEL = {
    "EQUITY_INDEX": "Equity Index", "RATES_10Y": "10Y Interest Rate",
    "FX_USD": "US Dollar (FX)", "OIL": "Oil", "GOLD": "Gold",
}
FACTOR_ORDER = ["EQUITY_INDEX", "RATES_10Y", "FX_USD", "OIL", "GOLD"]

DEFAULT_CFG = {
    "portfolio": {
        "notional": 1_000_000.0,
        "weights": {"EQUITY_INDEX": 0.45, "RATES_10Y": 0.20, "FX_USD": 0.15, "OIL": 0.10, "GOLD": 0.10},
        "mapping": {"apply_rate_duration": True, "duration_years": 7.0, "convexity": 55.0},
    },
    "risk": {"confidence": 0.99, "horizon_days": 1, "training_window": 250},
    "limits": {"var_99": 0.04, "es_99": 0.06, "stress_loss": 0.20, "credit_expected_loss": 0.04},
    "stress": {"target_loss": 0.10, "bounds": {
        "EQUITY_INDEX": [-0.30, 0.0], "RATES_10Y": [0.0, 0.03], "FX_USD": [-0.15, 0.15],
        "OIL": [-0.25, 0.25], "GOLD": [-0.25, 0.25]}},
    "monitoring": {"warning_threshold": 0.10, "breach_threshold": 0.25},
    "credit": {"lgd_baseline": 0.45},
}

CSS = """
<style>
.block-container {padding-top: 2rem; max-width: 1250px;}
.hero {background: linear-gradient(135deg,#0f172a 0%,#312e81 55%,#0e7490 100%);
  padding: 2.2rem 2.4rem; border-radius: 22px; color:#fff; margin-bottom: 1.2rem;
  border: 1px solid rgba(255,255,255,.10); box-shadow: 0 10px 30px rgba(0,0,0,.25);}
.hero h1 {font-size: 2.6rem; margin: 0 0 .2rem 0; padding: 0; color:#fff; line-height:1.15;}
.hero .sub {color: rgba(255,255,255,.88); font-size: 1.12rem; margin: .3rem 0 .6rem 0;}
.pill {display:inline-block; padding:.22rem .75rem; margin:.25rem .35rem 0 0; border-radius:999px;
  background: rgba(255,255,255,.14); font-size:.8rem; color:#fff; border:1px solid rgba(255,255,255,.15);}
.phead {display:flex; align-items:center; gap:1rem; margin-bottom:.8rem;
  padding: 1rem 1.3rem; border-radius: 18px;
  background: linear-gradient(90deg, rgba(99,102,241,.22), rgba(20,184,166,.10));
  border: 1px solid rgba(99,102,241,.35);}
.phead .pi {font-size: 2.2rem;}
.phead h2 {margin:0; padding:0; font-size:1.6rem;}
.phead p {margin:.1rem 0 0 0; opacity:.82;}
.kpi {background: rgba(128,128,128,.10); border: 1px solid rgba(128,128,128,.22);
  border-left: 5px solid var(--c,#6366F1); border-radius: 14px; padding: .85rem 1rem; margin-bottom:.6rem; min-height: 128px;}
.kpi .l {font-size:.74rem; text-transform:uppercase; letter-spacing:.06em; opacity:.72;}
.kpi .v {font-size:1.85rem; font-weight:700; line-height:1.2; margin:.1rem 0;}
.kpi .s {font-size:.82rem; opacity:.78;}
.callout {border-left: 5px solid var(--c,#6366F1); background: rgba(128,128,128,.10);
  border-radius: 10px; padding: .8rem 1rem; margin: .5rem 0 .9rem 0; line-height:1.5;}
.card {background: rgba(128,128,128,.09); border: 1px solid rgba(128,128,128,.22);
  border-radius: 16px; padding: 1rem 1.1rem; margin-bottom:.7rem; height: calc(100% - .7rem);}
.card h4 {margin: 0 0 .35rem 0; padding:0; font-size: 1.05rem;}
.card p {margin:.2rem 0; opacity:.88; font-size:.93rem; line-height:1.45;}
.step {text-align:center; background: rgba(99,102,241,.10); border:1px solid rgba(99,102,241,.35);
  border-radius:16px; padding:.9rem .6rem; height:100%; min-height:150px;}
.step .n {font-size:1.7rem;}
.step b {display:block; margin:.2rem 0;}
.step span {font-size:.82rem; opacity:.82; line-height:1.35; display:block;}
.badge {display:inline-block; padding:.12rem .6rem; border-radius:999px; font-size:.75rem; font-weight:700;
  background: var(--c,#6366F1); color:#fff; margin-right:.3rem;}
.chip {display:inline-block; padding:.28rem .8rem; margin:.2rem .3rem .2rem 0; border-radius:10px;
  background: rgba(20,184,166,.15); border:1px solid rgba(20,184,166,.45); font-size:.85rem;}
.big {font-size:2.4rem; font-weight:800; line-height:1.1;}
.formula {text-align:center; font-size:1.25rem; font-weight:700; padding:.6rem; border-radius:14px;
  background: rgba(99,102,241,.14); border:1px dashed rgba(99,102,241,.6); margin:.5rem 0 1rem 0;}
</style>
"""

# ----------------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------------
def md(text: str) -> None:
    """Render markdown/HTML. '$' is escaped so Streamlit never mistakes money for LaTeX."""
    st.markdown(text.replace("$", "&#36;"), unsafe_allow_html=True)


def plot(fig: go.Figure, key: str | None = None) -> None:
    try:
        st.plotly_chart(fig, width="stretch", key=key)
    except TypeError:  # older Streamlit versions
        st.plotly_chart(fig, use_container_width=True, key=key)


def table(df: pd.DataFrame, **kw) -> None:
    try:
        st.dataframe(df, width="stretch", hide_index=True, **kw)
    except TypeError:
        st.dataframe(df, use_container_width=True, hide_index=True, **kw)


def pct(x: float, d: int = 2) -> str:
    return "n/a" if pd.isna(x) else f"{x:.{d}%}"


def usd(x: float) -> str:
    if pd.isna(x):
        return "n/a"
    sign = "-" if x < 0 else ""
    x = abs(x)
    if x >= 1_000_000:
        return f"{sign}${x / 1_000_000:,.2f}M"
    return f"{sign}${x:,.0f}"


def kpi(label: str, value: str, sub: str = "", color: str = INDIGO) -> None:
    md(f'<div class="kpi" style="--c:{color}"><div class="l">{label}</div>'
       f'<div class="v">{value}</div><div class="s">{sub}</div></div>')


def callout(title: str, body: str, kind: str = "info") -> None:
    color = {"info": INDIGO, "good": GREEN, "warn": AMBER, "bad": RED}[kind]
    icon = {"info": "💡", "good": "✅", "warn": "⚠️", "bad": "🚨"}[kind]
    md(f'<div class="callout" style="--c:{color}"><b>{icon} {title}</b><br>{body}</div>')


def card(title: str, body: str) -> None:
    md(f'<div class="card"><h4>{title}</h4><p>{body}</p></div>')


def header(icon: str, title: str, tagline: str) -> None:
    md(f'<div class="phead"><div class="pi">{icon}</div><div><h2>{title}</h2><p>{tagline}</p></div></div>')


def style_fig(fig: go.Figure, height: int = 420, legend: bool = True) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=90, b=10), showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0),
    )
    return fig


def model_name(m: str) -> str:
    return MODEL_LABEL.get(m, m)


def factor_name(f: str) -> str:
    return FACTOR_LABEL.get(f, f)


@st.cache_data(show_spinner=False)
def load_table(name: str) -> pd.DataFrame:
    p = RESULTS / f"{name}.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_json(name: str) -> dict:
    p = REPORTS / name
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    except Exception:
        return {}


@st.cache_data(show_spinner=False)
def load_cfg() -> dict:
    try:
        from riskforge.utils.config import load_config
        return load_config("base.yaml")
    except Exception:
        return DEFAULT_CFG


TABLES = [
    "market_risk_latest", "market_risk_results", "model_comparison", "statistical_tests",
    "market_model_stability", "stress_scenarios", "sensitivity_equity", "reverse_stress_solution",
    "reverse_stress_multi_start", "attribution_volatility", "attribution_scenario_ranking",
    "credit_expected_loss", "credit_model_metrics", "credit_stress", "credit_segment_performance",
    "credit_calibration", "credit_predictions", "credit_data_quality", "risk_limits",
    "model_inventory", "drift_metrics", "validation_findings", "sql_reconciliation", "garch_volatility",
]


def section(title: str, sub: str = "") -> None:
    st.markdown(f"### {title}")
    if sub:
        md(f"<span style='opacity:.8'>{sub}</span>")


def need(d: dict, *names: str) -> bool:
    missing = [n for n in names if d.get(n) is None or d[n].empty]
    if missing:
        st.warning("Results not found: " + ", ".join(missing) +
                   ". Run `python scripts/run_pipeline.py` first to generate them.")
        return False
    return True


# ----------------------------------------------------------------------------
# Shared computations (single source of truth for the numbers quoted in text)
# ----------------------------------------------------------------------------
def summary_numbers(d: dict, cfg: dict) -> dict:
    s: dict = {"notional": float(cfg["portfolio"].get("notional", 1_000_000))}
    lat = d["market_risk_latest"]
    if not lat.empty:
        r = lat.loc[lat["VaR"].idxmax()]
        s.update(var=float(r["VaR"]), es=float(r["ES"]), var_model=r["model"])
    comp, tests = d["model_comparison"], d["statistical_tests"]
    if not comp.empty and not tests.empty:
        m = comp.merge(tests[["model_id", "overall_pass", "p_value", "christ_p_value"]], on="model_id")
        m["gap"] = (m["exception_rate"] - m["target_rate"]).abs()
        passed = m[m["overall_pass"]]
        best = (passed if not passed.empty else m).sort_values("gap").iloc[0]
        s.update(best_model=best["model_id"], best_rate=float(best["exception_rate"]),
                 target=float(best["target_rate"]), n_pass=int(m["overall_pass"].sum()), n_models=len(m))
    st_df = d["stress_scenarios"]
    if not st_df.empty:
        sc = st_df.groupby("scenario_id", as_index=False).agg(loss=("portfolio_loss", "first"),
                                                              desc=("description", "first"))
        w = sc.sort_values("loss", ascending=False).iloc[0]
        s.update(worst_stress=float(w["loss"]), worst_stress_id=w["scenario_id"])
    cr = d["credit_expected_loss"]
    if not cr.empty:
        a = cr[cr["segment"] == "ALL"].iloc[0]
        s.update(el=float(a["expected_loss"]), ead=float(a["ead"]), el_rate=float(a["expected_loss_rate"]),
                 mean_pd=float(a["mean_pd"]))
    at = d["attribution_volatility"]
    if not at.empty:
        t = at.sort_values("pct_of_portfolio_variance", ascending=False).iloc[0]
        s.update(top_factor=t["risk_factor"], top_share=float(t["pct_of_portfolio_variance"]),
                 top_weight=float(t["weight"]))
    lim = d["risk_limits"]
    if not lim.empty:
        s.update(n_limits=len(lim), n_breach=int((lim["status"] == "BREACH").sum()))
    return s


# ----------------------------------------------------------------------------
# PAGE: Start here
# ----------------------------------------------------------------------------
def page_home(d: dict, cfg: dict) -> None:
    s = summary_numbers(d, cfg)
    pills = "".join(f'<span class="pill">{p}</span>' for p in
                    ["Python", "pandas · NumPy · SciPy", "statsmodels (GARCH)", "scikit-learn · XGBoost",
                     "SQL · SQLAlchemy", "Plotly · Streamlit", "pytest · GitHub Actions"])
    md(f"""<div class="hero"><h1>◈ RiskSphere</h1>
<div class="sub"><b>How much money can a portfolio lose - and can we trust the answer?</b><br>
An end-to-end risk-analytics platform that measures market risk, credit risk and stress losses,
checks whether its own models are honest, and flags when limits are broken.</div>{pills}</div>""")

    c1, c2 = st.columns([3, 1])
    with c1:
        callout("About the data",
                "All numbers come from a <b>reproducible synthetic dataset</b> (fixed random seed), so anyone can re-run the "
                "pipeline and get identical results. This is an educational portfolio project - not a production bank system.", "info")
    with c2:
        st.link_button("⭐ View code on GitHub", GITHUB)

    # --- 30 second story ------------------------------------------------------
    section("🧭 The 30-second story")
    a, b, c = st.columns(3)
    with a:
        card("❓ The problem",
             "Banks and funds must answer: <i>How much could we lose tomorrow? In a crash? How much will borrowers fail to repay? "
             "And are our models actually reliable?</i> Most student projects stop at one model and one score. Real risk teams cannot.")
    with b:
        card("🛠️ What I built",
             "A full pipeline: <b>4 market-risk models</b> (VaR &amp; Expected Shortfall), <b>2 credit-default models</b>, "
             "stress &amp; reverse-stress tests, risk attribution, statistical backtests, drift monitoring, risk limits, "
             "SQL storage and <b>49 automated tests</b>.")
    with c:
        top = factor_name(s.get("top_factor", "")) if s.get("top_factor") else "equities"
        card("🎯 What I found",
             f"The best-calibrated model was <b>{model_name(s.get('best_model', 'GARCH'))}</b>; "
             f"<b>{top}</b> drives most of the risk; the worst stress costs <b>{pct(s.get('worst_stress', np.nan), 1)}</b>; "
             f"and the credit book <b>breaches its loss limit</b> - the dashboard catches it automatically.")

    # --- pipeline -------------------------------------------------------------
    section("🔄 How the platform works", "Data goes in on the left, decisions come out on the right.")
    steps = [
        ("🗄️", "1. Data", "Synthetic market prices for 5 risk factors + 4,000 loan records; quality checks &amp; version hash"),
        ("📉", "2. Market risk", "Historical, Parametric, EWMA &amp; GARCH models estimate daily VaR and Expected Shortfall"),
        ("🏦", "3. Credit risk", "Logistic &amp; XGBoost predict default; Expected Loss = PD × LGD × EAD"),
        ("✅", "4. Validation", "Kupiec &amp; Christoffersen backtests, PSI drift, ROC/KS/Brier checks"),
        ("💥", "5. Stress", "Crash scenarios and a solver that finds the smallest shock causing a 10% loss"),
        ("🛡️", "6. Governance", "Risk limits, model inventory, findings log, Python↔SQL reconciliation"),
    ]
    cols = st.columns(6)
    for col, (ic, t, tx) in zip(cols, steps):
        with col:
            md(f'<div class="step"><div class="n">{ic}</div><b>{t}</b><span>{tx}</span></div>')

    # --- headline numbers -----------------------------------------------------
    section("📊 Headline results", "The eight numbers that summarise the whole project.")
    r1 = st.columns(4)
    with r1[0]:
        kpi("Portfolio analysed", usd(s["notional"]), "5 risk factors · daily data 2015-2024", INDIGO)
    with r1[1]:
        kpi("Bad-day loss limit (1-day 99% VaR)", pct(s.get("var", np.nan)),
            f"≈ {usd(s.get('var', np.nan) * s['notional'])} · most cautious model: {model_name(s.get('var_model', ''))}", TEAL)
    with r1[2]:
        kpi("Average loss on a very bad day (ES)", pct(s.get("es", np.nan)),
            f"≈ {usd(s.get('es', np.nan) * s['notional'])} when VaR is exceeded", SKY)
    with r1[3]:
        kpi("Most trustworthy model", model_name(s.get("best_model", "")),
            f"{pct(s.get('best_rate', np.nan))} breaches vs {pct(s.get('target', 0.01))} target · {s.get('n_pass', 0)}/{s.get('n_models', 0)} models passed both tests", GREEN)
    r2 = st.columns(4)
    with r2[0]:
        kpi("Worst stress scenario", pct(s.get("worst_stress", np.nan), 1),
            str(s.get("worst_stress_id", "")).replace("_", " ").title(), RED)
    with r2[1]:
        kpi("Expected credit loss", usd(s.get("el", np.nan)),
            f"{pct(s.get('el_rate', np.nan), 1)} of {usd(s.get('ead', np.nan))} lent", AMBER)
    with r2[2]:
        kpi("Biggest risk driver", factor_name(s.get("top_factor", "")),
            f"{pct(s.get('top_share', np.nan), 0)} of risk from only {pct(s.get('top_weight', np.nan), 0)} of the money", PINK)
    with r2[3]:
        ok = s.get("n_limits", 0) - s.get("n_breach", 0)
        kpi("Risk limits", f"{ok} of {s.get('n_limits', 0)} OK",
            (f"{s.get('n_breach')} breach flagged: " + ", ".join(
                str(m).replace("_", " ") for m in d["risk_limits"].loc[d["risk_limits"]["status"] == "BREACH", "metric"]))
            if s.get("n_breach", 0) else "all within limits",
            RED if s.get("n_breach", 0) else GREEN)

    # --- portfolio ------------------------------------------------------------
    section("💼 The portfolio under the microscope",
            "A 5-asset portfolio, hypothetically invested for 10 years. Everything on the other pages is about this portfolio.")
    left, right = st.columns([1, 2])
    weights = cfg["portfolio"]["weights"]
    with left:
        fig = go.Figure(go.Pie(
            labels=[factor_name(k) for k in FACTOR_ORDER if k in weights],
            values=[weights[k] for k in FACTOR_ORDER if k in weights], hole=.55,
            marker=dict(colors=[INDIGO, TEAL, AMBER, PINK, SKY]), textinfo="label+percent",
            hovertemplate="%{label}: %{percent}<extra></extra>"))
        fig.update_layout(title="Where the money is invested")
        plot(style_fig(fig, 380, legend=False), key="home_donut")
    with right:
        bt = load_table("backtest_garch_var")
        if not bt.empty:
            bt["forecast_date"] = pd.to_datetime(bt["forecast_date"])
            value = s["notional"] * (1 + bt["realized_return"]).cumprod()
            fig = go.Figure(go.Scatter(x=bt["forecast_date"], y=value, mode="lines", fill="tozeroy",
                                       line=dict(color=TEAL, width=2), fillcolor="rgba(20,184,166,.18)",
                                       hovertemplate="%{x|%d %b %Y}<br>$%{y:,.0f}<extra></extra>"))
            fig.update_layout(title="Simulated value of the portfolio over time (synthetic data)",
                              yaxis_title="Portfolio value ($)")
            fig.update_yaxes(rangemode="normal")
            plot(style_fig(fig, 380, legend=False), key="home_value")

    # --- key findings --------------------------------------------------------
    section("🔎 Key findings (in plain English)")
    comp = d["model_comparison"].set_index("model_id") if not d["model_comparison"].empty else pd.DataFrame()
    if not comp.empty and "garch_var" in comp.index:
        g, e = comp.loc["garch_var"], comp.loc["ewma_var"]
        callout("Not all risk models are equally honest",
                f"A 99% model should be wrong on about 1 day in 100. GARCH was wrong on <b>{pct(g['exception_rate'])}</b> of days; "
                f"the simple Parametric &amp; EWMA models on <b>{pct(e['exception_rate'])}</b> - they under-estimated danger and "
                f"<b>failed</b> the statistical test.", "good")
    if s.get("top_factor"):
        neg = d["attribution_volatility"][d["attribution_volatility"]["pct_of_portfolio_variance"] < 0]
        hedge = (f" {factor_name(neg.iloc[0]['risk_factor'])} actually <i>reduces</i> risk - it acts as a hedge." if not neg.empty else "")
        callout("Money is not the same as risk",
                f"{factor_name(s['top_factor'])} is {pct(s['top_weight'], 0)} of the portfolio but creates <b>{pct(s['top_share'], 0)}</b> of its risk." + hedge, "info")
    if s.get("worst_stress") is not None:
        callout("Crash test",
                f"A 2008-style crash would cost <b>{pct(s['worst_stress'], 1)}</b> (≈ {usd(s['worst_stress'] * s['notional'])}) - "
                f"about {s['worst_stress'] / max(s.get('var', 1e-9), 1e-9):.1f}× the 'normal bad day' VaR, which is why stress tests exist.", "warn")
    cm = d["credit_model_metrics"]
    if not cm.empty and {"logistic_pd", "xgboost_pd"} <= set(cm["model_id"]):
        lg = cm.set_index("model_id")
        rank_best = lg["roc_auc"].idxmax()
        calib_best = lg["brier_score"].idxmin()
        if rank_best != calib_best:
            callout("Ranking borrowers vs. predicting probabilities",
                    f"{model_name(rank_best)} ranks risky borrowers slightly better (AUC {lg.loc[rank_best, 'roc_auc']:.3f} vs {lg.loc[calib_best, 'roc_auc']:.3f}), "
                    f"but {model_name(calib_best)} gives far more accurate default probabilities (Brier {lg.loc[calib_best, 'brier_score']:.3f} vs {lg.loc[rank_best, 'brier_score']:.3f}; "
                    f"actual default rate {pct(lg.loc[calib_best, 'observed_default_rate'], 1)}). Expected Loss needs accurate probabilities, so {model_name(calib_best)} feeds the loss calculation.", "info")
    if s.get("n_breach"):
        br = d["risk_limits"][d["risk_limits"]["status"] == "BREACH"].iloc[0]
        callout("The governance layer works",
                f"{str(br['metric']).replace('_', ' ').capitalize()} is <b>{br['utilization']:.0%} of its limit</b>. The system flagged it "
                "as a finding and recommends escalation - exactly what a risk-control framework should do.", "bad")

    # --- tour -----------------------------------------------------------------
    section("🗺️ Take the tour")
    tour = [
        (P_MKT, "See daily loss forecasts, in dollars, for four models."),
        (P_BT, "Did the models tell the truth? Statistical report cards."),
        (P_ST, "Crash scenarios + an interactive 'build your own crash' lab."),
        (P_ATTR, "Which asset is really responsible for the risk?"),
        (P_CR, "Predict loan defaults and compute expected loss."),
        (P_GOV, "Limits, drift monitoring, findings and model inventory."),
        (P_ABOUT, "Tech stack, methodology and limitations."),
    ]
    cols = st.columns(4)
    for i, (pg, tx) in enumerate(tour):
        with cols[i % 4]:
            card(pg, tx)
            st.button("Open →", key=f"tour_{i}", on_click=lambda p=pg: st.session_state.update(nav=p))


# ----------------------------------------------------------------------------
# PAGE: Market risk
# ----------------------------------------------------------------------------
def page_market(d: dict, cfg: dict) -> None:
    header("📉", "Market Risk", "How much could the portfolio lose tomorrow?")
    if not need(d, "market_risk_latest", "market_risk_results"):
        return
    lat, res = d["market_risk_latest"], d["market_risk_results"].copy()
    res["forecast_date"] = pd.to_datetime(res["forecast_date"])
    conf = float(cfg["risk"]["confidence"])

    a, b = st.columns(2)
    with a:
        card("📏 Value-at-Risk (VaR) in one sentence",
             f"“On a normal day, I'm {conf:.0%} sure I won't lose more than <b>this</b>.” "
             f"At {conf:.0%} confidence, a loss bigger than VaR should happen only about <b>1 day in 100</b>.")
    with b:
        card("🌪️ Expected Shortfall (ES) in one sentence",
             "“If it <i>is</i> one of those bad days, how bad is it <b>on average</b>?” "
             "ES looks inside the worst 1% and is always at least as big as VaR.")

    section("💵 Try it: what does that mean in dollars?")
    notional = st.number_input("Portfolio size ($)", min_value=10_000, max_value=1_000_000_000,
                               value=int(cfg["portfolio"].get("notional", 1_000_000)), step=50_000)
    cols = st.columns(len(lat))
    for col, (_, r) in zip(cols, lat.iterrows()):
        with col:
            kpi(model_name(r["model"]), usd(r["VaR"] * notional),
                f"VaR {pct(r['VaR'])} · ES {usd(r['ES'] * notional)} ({pct(r['ES'])})", MODEL_COLOR.get(r["model"], INDIGO))
    fig = go.Figure()
    names = [model_name(m) for m in lat["model"]]
    fig.add_bar(x=names, y=lat["VaR"] * 100, name="VaR (normal bad day)", marker_color=INDIGO,
                text=[f"{v:.2%}" for v in lat["VaR"]], textposition="outside")
    fig.add_bar(x=names, y=lat["ES"] * 100, name="ES (average on the worst days)", marker_color=PINK,
                text=[f"{v:.2%}" for v in lat["ES"]], textposition="outside")
    fig.update_layout(barmode="group", title=f"Latest 1-day forecasts ({lat['forecast_date'].iloc[0]})",
                      yaxis_title="% of portfolio")
    plot(style_fig(fig, 380), key="mk_latest")
    callout("Why do the models disagree?",
            "Each model makes a different assumption about the future. GARCH reacts quickly when markets get "
            "jumpy, so it is the most cautious right now; Historical only looks at the last 250 days; "
            "Parametric &amp; EWMA assume returns follow a bell curve, which can understate rare crashes.", "info")

    t1, t2, t3 = st.tabs(["🔍 Forecast vs. reality", "🌊 Volatility (GARCH)", "⚖️ All models together"])
    with t1:
        model = st.selectbox("Choose a model", list(MODEL_LABEL)[:4], format_func=model_name, index=3)
        bt = load_table(f"backtest_{model}")
        if bt.empty:
            st.info("Backtest file not found.")
        else:
            bt["forecast_date"] = pd.to_datetime(bt["forecast_date"])
            exc = bt[bt["exception_flag"].astype(bool)]
            fig = go.Figure()
            fig.add_scatter(x=bt["forecast_date"], y=bt["realized_loss"] * 100, mode="lines", name="Actual daily loss",
                            line=dict(color=SLATE, width=1), opacity=.7)
            fig.add_scatter(x=bt["forecast_date"], y=bt["var"] * 100, mode="lines", name="VaR limit (model forecast)",
                            line=dict(color=MODEL_COLOR[model], width=2))
            fig.add_scatter(x=exc["forecast_date"], y=exc["realized_loss"] * 100, mode="markers",
                            name=f"Breaches ({len(exc)})", marker=dict(color=RED, size=9, symbol="x"))
            fig.update_layout(title=f"{model_name(model)}: did actual losses stay under the VaR line?",
                              yaxis_title="Daily loss (% of portfolio)  -  negative = profit")
            fig.update_xaxes(rangeslider_visible=True)
            plot(style_fig(fig, 480), key="mk_ts")
            exp = len(bt) * (1 - conf)
            st.caption(f"Over {len(bt):,} out-of-sample days the loss exceeded VaR on {len(exc)} days; "
                       f"a perfect {conf:.0%} model would show about {exp:.0f}. Drag the slider under the chart to zoom into any period.")
    with t2:
        gv = d["garch_volatility"]
        if gv.empty:
            st.info("GARCH volatility file not found.")
        else:
            gv = gv.copy()
            gv["forecast_date"] = pd.to_datetime(gv["forecast_date"])
            gv["ann"] = gv["volatility"] * np.sqrt(252) * 100
            fig = go.Figure(go.Scatter(x=gv["forecast_date"], y=gv["ann"], mode="lines", fill="tozeroy",
                                       line=dict(color=TEAL, width=1.6), fillcolor="rgba(20,184,166,.20)",
                                       hovertemplate="%{x|%d %b %Y}<br>%{y:.1f}% per year<extra></extra>"))
            fig.update_layout(title="Market 'nervousness' estimated by GARCH (annualised volatility)", yaxis_title="% per year")
            plot(style_fig(fig, 400, legend=False), key="mk_garch")
            gp = load_json("garch_parameters.json")
            if gp:
                c = st.columns(3)
                with c[0]:
                    kpi("α (reaction)", f"{gp.get('alpha', np.nan):.2f}", "How strongly volatility jumps after a big move", TEAL)
                with c[1]:
                    kpi("β (memory)", f"{gp.get('beta', np.nan):.2f}", "How long that nervousness lingers", INDIGO)
                with c[2]:
                    kpi("α + β", f"{gp.get('alpha', 0) + gp.get('beta', 0):.2f}", "Below 1 → volatility settles back to normal", GREEN)
            st.caption("Volatility comes in clusters: calm periods are followed by calm, turbulent by turbulent. "
                       "GARCH models exactly this, which is why its VaR line moves with the market.")
    with t3:
        fig = go.Figure()
        for m in list(MODEL_LABEL)[:4]:
            g = res[res["model"] == m]
            fig.add_scatter(x=g["forecast_date"], y=g["VaR"] * 100, mode="lines", name=model_name(m),
                            line=dict(color=MODEL_COLOR[m], width=1.6))
        fig.update_layout(title="99% VaR forecast through time, all four models", yaxis_title="VaR (% of portfolio)")
        fig.update_xaxes(rangeslider_visible=True)
        plot(style_fig(fig, 460), key="mk_all")
        avg = res.groupby("model")[["VaR", "ES"]].mean().reset_index()
        avg["Model"] = avg["model"].map(model_name)
        avg["Average VaR"] = avg["VaR"].map(pct)
        avg["Average ES"] = avg["ES"].map(pct)
        with st.expander("Show average VaR / ES per model"):
            table(avg[["Model", "Average VaR", "Average ES"]])


# ----------------------------------------------------------------------------
# PAGE: Backtesting
# ----------------------------------------------------------------------------
def page_backtest(d: dict, cfg: dict) -> None:
    header("✅", "Backtesting", "Did the models tell the truth? A statistical report card.")
    if not need(d, "model_comparison", "statistical_tests"):
        return
    comp, tests = d["model_comparison"], d["statistical_tests"]
    conf = float(cfg["risk"]["confidence"])
    n = int(comp["n_forecasts"].iloc[0])
    expected = n * (1 - conf)

    callout("The idea",
            f"If a model says “{conf:.0%} sure I won't lose more than X”, then over {n:,} days it should be wrong on about "
            f"<b>{expected:.0f} days</b> ({1 - conf:.0%}). <b>Too many</b> breaches → the model underestimates risk (dangerous). "
            "<b>Too few</b> → it is too cautious (expensive). Two tests judge this:", "info")
    a, b = st.columns(2)
    with a:
        card("🎯 Kupiec test - “right number of breaches?”", "Compares the observed breach rate with the promised 1%. "
             "p-value below 0.05 = the model <b>fails</b>.")
    with b:
        card("🔗 Christoffersen test - “are breaches spread out?”", "Breaches that come in clumps mean the model reacts too slowly to "
             "turbulent periods. p-value below 0.05 = the model <b>fails</b>.")

    section("🏅 Report cards")
    cols = st.columns(len(tests))
    for col, (_, r) in zip(cols, tests.iterrows()):
        with col:
            kup, chr_ = (not r["reject_null_at_5pct"]), (not r["christ_reject_null_at_5pct"])
            overall = bool(r["overall_pass"])
            badge = f'<span class="badge" style="--c:{GREEN if overall else RED}">{"PASS" if overall else "FAIL"}</span>'
            md(f"""<div class="card" style="border-left:5px solid {GREEN if overall else RED}">
<h4>{model_name(r['model_id'])} {badge}</h4>
<p><b>{int(r['n_exceptions'])}</b> breaches ({pct(r['observed_rate'])}) vs {expected:.0f} expected</p>
<p>{'✅' if kup else '❌'} Kupiec p = {r['p_value']:.3f}</p>
<p>{'✅' if chr_ else '❌'} Christoffersen p = {r['christ_p_value']:.3f}</p></div>""")

    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure()
        fig.add_bar(x=[model_name(m) for m in comp["model_id"]], y=comp["n_exceptions"],
                    marker_color=[MODEL_COLOR.get(m, INDIGO) for m in comp["model_id"]],
                    text=comp["n_exceptions"], textposition="outside", name="Observed breaches")
        fig.add_hline(y=expected, line_dash="dash", line_color=AMBER,
                      annotation_text=f"Expected ≈ {expected:.0f}", annotation_position="top left")
        fig.update_layout(title="How many times was VaR breached?", yaxis_title="Number of breaches")
        plot(style_fig(fig, 400, legend=False), key="bt_exc")
    with c2:
        fig = go.Figure()
        fig.add_bar(x=[model_name(m) for m in tests["model_id"]], y=tests["p_value"], name="Kupiec p-value", marker_color=INDIGO)
        fig.add_bar(x=[model_name(m) for m in tests["model_id"]], y=tests["christ_p_value"], name="Christoffersen p-value", marker_color=PINK)
        fig.add_hline(y=0.05, line_dash="dash", line_color=RED, annotation_text="Below this line → FAIL",
                      annotation_position="top left")
        fig.update_layout(barmode="group", title="Test scores (higher is better)", yaxis_title="p-value")
        plot(style_fig(fig, 400), key="bt_p")

    stab = d["market_model_stability"]
    if not stab.empty:
        section("🗓️ Was the model reliable in every year?", "Breach rate per calendar year. Target is 1% (white); red = too many breaches, blue = too few.")
        s2 = stab[stab["n_forecasts"] >= 50].copy()
        s2["year"] = s2["period_end"].astype(str).str[:4]
        pv = s2.pivot(index="model_id", columns="year", values="exception_rate") * 100
        pv = pv.reindex([m for m in list(MODEL_LABEL)[:4] if m in pv.index])
        fig = go.Figure(go.Heatmap(
            z=pv.values, x=list(pv.columns), y=[model_name(m) for m in pv.index], zmid=1.0, zmin=0, zmax=3,
            colorscale=[[0, "#38BDF8"], [.33, "#F8FAFC"], [1, "#EF4444"]],
            text=np.round(pv.values, 1), texttemplate="%{text}%", colorbar=dict(title="Breach %"),
            hovertemplate="%{y}, %{x}: %{z:.2f}%<extra></extra>"))
        fig.update_layout(title="Yearly breach rate (%)")
        plot(style_fig(fig, 320, legend=False), key="bt_heat")
        st.caption("2015 is excluded (only ~10 forecast days). One quiet year with 0% breaches is not proof of a good model; one bad year is not proof of a bad one.")

    if comp["model_id"].isin(["garch_var"]).any():
        bad = tests[~tests["overall_pass"]]["model_id"].map(model_name).tolist()
        callout("Takeaway",
                f"{', '.join(bad) if bad else 'No model'} failed the breach-count test: they assume returns follow a bell curve and "
                "so understate crashes. <b>GARCH</b>, which lets volatility change over time, was closest to the promised 1%. "
                "Passing a test is still <i>not proof</i> a model is correct - it only means we found no evidence it is wrong.", "good")
    with st.expander("See the full statistical output"):
        table(tests)


# ----------------------------------------------------------------------------
# PAGE: Stress testing
# ----------------------------------------------------------------------------
def rate_return(dy: float, cfg: dict) -> float:
    m = cfg["portfolio"].get("mapping", {})
    if not m.get("apply_rate_duration", True):
        return dy
    return -float(m.get("duration_years", 7.0)) * dy + 0.5 * float(m.get("convexity", 55.0)) * dy ** 2


def page_stress(d: dict, cfg: dict) -> None:
    header("💥", "Stress Testing", "What if something extreme - but plausible - happens?")
    if not need(d, "stress_scenarios"):
        return
    st_df = d["stress_scenarios"]
    weights, notional = cfg["portfolio"]["weights"], float(cfg["portfolio"].get("notional", 1_000_000))
    limit = float(cfg.get("limits", {}).get("stress_loss", 0.20))
    callout("Why stress test?",
            "VaR describes a <i>normal</i> bad day. Stress tests ask about <b>rare, severe events</b> - an equity crash, "
            "a surprise rate hike, an oil shock - by applying a shock to every asset and adding up the damage.", "info")

    sc = st_df.groupby("scenario_id", as_index=False).agg(loss=("portfolio_loss", "first"), desc=("description", "first"))
    sc = sc.sort_values("loss", ascending=False).reset_index(drop=True)
    cols = st.columns(len(sc))
    for col, (_, r) in zip(cols, sc.iterrows()):
        with col:
            gain = r["loss"] < 0
            kpi(str(r["scenario_id"]).replace("_", " ").title(),
                ("+" if gain else "-") + pct(abs(r["loss"])),
                f"{'gain' if gain else 'loss'} ≈ {usd(abs(r['loss']) * notional)} · {r['desc']}", GREEN if gain else RED)

    t1, t2, t3 = st.tabs(["📋 Scenario results", "🧪 Build your own crash", "🔄 Reverse stress test"])
    with t1:
        fig = go.Figure(go.Bar(
            y=[s.replace("_", " ").title() for s in sc["scenario_id"]][::-1], x=(sc["loss"] * 100)[::-1], orientation="h",
            marker_color=[GREEN if v < 0 else RED for v in sc["loss"]][::-1],
            text=[f"{v:.2%}" for v in sc["loss"]][::-1], textposition="outside"))
        fig.add_vline(x=limit * 100, line_dash="dash", line_color=AMBER, annotation_text=f"Stress limit {limit:.0%}")
        fig.update_layout(title="Portfolio loss under each scenario (% of portfolio)", xaxis_title="Loss (negative = gain)")
        plot(style_fig(fig, 340, legend=False), key="st_bar")

        pick = st.selectbox("Open a scenario to see which asset hurt", sc["scenario_id"].tolist(),
                            format_func=lambda s: s.replace("_", " ").title())
        g = st_df[st_df["scenario_id"] == pick].set_index("risk_factor").reindex(FACTOR_ORDER).dropna(subset=["factor_contribution"])
        contrib = (g["factor_contribution"] * 100).tolist()
        fig = go.Figure(go.Waterfall(
            x=[factor_name(f) for f in g.index] + ["Total P&L"],
            measure=["relative"] * len(g) + ["total"], y=contrib + [sum(contrib)],
            text=[f"{v:+.2f}%" for v in contrib] + [f"{sum(contrib):+.2f}%"], textposition="outside",
            increasing=dict(marker=dict(color=GREEN)), decreasing=dict(marker=dict(color=RED)),
            totals=dict(marker=dict(color=INDIGO)), connector=dict(line=dict(color=SLATE))))
        fig.update_layout(title=f"{pick.replace('_', ' ').title()}: who made / lost the money?", yaxis_title="Contribution to P&L (% of portfolio)")
        plot(style_fig(fig, 420, legend=False), key="st_wf")
        shocks = g[["shock"]].copy()
        shocks.index = [factor_name(f) for f in shocks.index]
        st.caption("Shocks applied: " + " · ".join(
            f"{k}: {v:+.1%}" if k != "10Y Interest Rate" else f"{k}: {v * 1e4:+.0f} bp" for k, v in shocks["shock"].items()))

        se = d["sensitivity_equity"]
        if not se.empty:
            fig = go.Figure(go.Scatter(x=se["shock"] * 100, y=se["portfolio_loss"] * 100, mode="lines+markers",
                                       line=dict(color=INDIGO, width=3), marker=dict(size=9)))
            fig.add_hline(y=0, line_color=SLATE, line_dash="dot")
            fig.update_layout(title="Sensitivity: portfolio loss vs. equity move", xaxis_title="Equity move (%)", yaxis_title="Portfolio loss (%)")
            plot(style_fig(fig, 340, legend=False), key="st_sens")
            slope = float(np.polyfit(se["shock"], se["portfolio_loss"], 1)[0])
            st.caption(f"Rule of thumb: every 10% equity fall costs about {abs(slope) * 10:.1%} of the whole portfolio (because equities are {weights.get('EQUITY_INDEX', 0):.0%} of it).")

    with t2:
        st.markdown("Drag the sliders to design your own market shock and watch the portfolio loss update **live**. "
                    "Start from a preset or from scratch.")
        presets: dict[str, dict[str, float]] = {"Calm (all zero)": {f: 0.0 for f in FACTOR_ORDER}}
        for sid, g in st_df.groupby("scenario_id"):
            presets[sid.replace("_", " ").title()] = g.set_index("risk_factor")["shock"].to_dict()
        keys = {"EQUITY_INDEX": "lab_eq", "RATES_10Y": "lab_rt", "FX_USD": "lab_fx", "OIL": "lab_oil", "GOLD": "lab_gold"}

        def to_slider(f: str, v: float) -> int:
            return int(round(v * 1e4)) if f == "RATES_10Y" else int(round(v * 100))

        def apply_preset() -> None:
            p = presets.get(st.session_state["lab_preset"], presets["Calm (all zero)"])
            for f, k in keys.items():
                st.session_state[k] = to_slider(f, p.get(f, 0.0))

        if "lab_preset" not in st.session_state:
            st.session_state["lab_preset"] = "Calm (all zero)"
        if "lab_eq" not in st.session_state:
            apply_preset()
        st.selectbox("Start from a preset", list(presets), key="lab_preset", on_change=apply_preset)
        c1, c2 = st.columns([1, 1])
        with c1:
            eq = st.slider("📈 Equity index (%)", -50, 30, key=keys["EQUITY_INDEX"])
            rt = st.slider("🏛️ 10Y interest rate (basis points)", -300, 400, step=5, key=keys["RATES_10Y"],
                           help="100 basis points = 1 percentage point. Rising rates push bond prices DOWN.")
            fx = st.slider("💵 US Dollar (%)", -30, 30, key=keys["FX_USD"])
            oil = st.slider("🛢️ Oil (%)", -60, 60, key=keys["OIL"])
            gold = st.slider("🥇 Gold (%)", -40, 40, key=keys["GOLD"])
        shock = {"EQUITY_INDEX": eq / 100, "RATES_10Y": rt / 1e4, "FX_USD": fx / 100, "OIL": oil / 100, "GOLD": gold / 100}
        mapped = {f: (rate_return(v, cfg) if f == "RATES_10Y" else v) for f, v in shock.items()}
        contrib = {f: weights.get(f, 0) * mapped[f] for f in FACTOR_ORDER}
        pnl = sum(contrib.values())
        loss = -pnl
        with c2:
            color = RED if loss > 0 else GREEN
            md(f'<div class="kpi" style="--c:{color}"><div class="l">Your scenario</div>'
               f'<div class="big" style="color:{color}">{"-" if loss > 0 else "+"}{abs(loss):.2%}</div>'
               f'<div class="s">{"Loss" if loss > 0 else "Gain"} of {usd(abs(loss) * notional)} on {usd(notional)}</div></div>')
            st.progress(float(min(max(loss, 0) / limit, 1.0)), text=f"Uses {max(loss, 0) / limit:.0%} of the {limit:.0%} stress-loss limit")
            if loss > limit:
                st.error("🚨 This scenario would breach the stress-loss limit.")
            fig = go.Figure(go.Bar(x=[factor_name(f) for f in FACTOR_ORDER], y=[contrib[f] * 100 for f in FACTOR_ORDER],
                                   marker_color=[GREEN if contrib[f] >= 0 else RED for f in FACTOR_ORDER],
                                   text=[f"{contrib[f] * 100:+.2f}%" for f in FACTOR_ORDER], textposition="outside"))
            fig.update_layout(title="Contribution to P&L (% of portfolio)")
            plot(style_fig(fig, 320, legend=False), key="st_lab")
        st.caption("Interest-rate shocks are converted to a bond-price move using duration and convexity: "
                   "return ≈ −duration × Δy + ½ × convexity × Δy².")

    with t3:
        rs = d["reverse_stress_solution"]
        if rs.empty:
            st.info("Reverse stress results not found.")
        else:
            target = float(rs["target_loss"].iloc[0])
            callout("Flip the question",
                    f"Instead of asking “what does this crash cost?”, we ask: <b>“what is the smallest market move that would lose {target:.0%}?”</b> "
                    "A numerical optimiser solves for it, subject to realistic bounds on each asset.", "info")
            bounds = cfg.get("stress", {}).get("bounds", {})
            rs = rs.set_index("risk_factor").reindex(FACTOR_ORDER).dropna(subset=["shock"])
            fig = go.Figure(go.Bar(x=[factor_name(f) for f in rs.index], y=rs["shock"] * 100,
                                   marker_color=[RED if v < 0 else AMBER for v in rs["shock"]],
                                   text=[f"{v:+.2%}" for v in rs["shock"]], textposition="outside"))
            fig.update_layout(title=f"The cheapest way to lose {target:.0%}", yaxis_title="Required shock (%)")
            plot(style_fig(fig, 380, legend=False), key="st_rev")
            hit = [factor_name(f) for f in rs.index if f in bounds and
                   (abs(rs.loc[f, "shock"] - bounds[f][0]) < 1e-6 or abs(rs.loc[f, "shock"] - bounds[f][1]) < 1e-6)]
            if hit:
                st.caption(f"{', '.join(hit)} reached the edge of the allowed range - the optimiser pushed it as far as permitted.")
            ms = d["reverse_stress_multi_start"]
            if not ms.empty:
                spread = float(ms["l2_norm"].max() - ms["l2_norm"].min())
                c = st.columns(3)
                with c[0]:
                    kpi("Solver starting points", f"{len(ms)}", "random starts tried", INDIGO)
                with c[1]:
                    kpi("Same answer every time?", "Yes ✅" if spread < 1e-4 else "No ⚠️", f"size of shock varies by only {spread:.1e}", GREEN if spread < 1e-4 else AMBER)
                with c[2]:
                    kpi("Constraints satisfied", f"{(ms['constraint_status'] == 'SATISFIED').sum()}/{len(ms)}", "all runs hit the 10% target", TEAL)
            st.caption("This is the minimum-size shock that works under the model's approximations - not the single worst-case scenario in the real world.")


# ----------------------------------------------------------------------------
# PAGE: Attribution
# ----------------------------------------------------------------------------
def page_attribution(d: dict, cfg: dict) -> None:
    header("🧩", "Risk Attribution", "Where does the risk actually come from?")
    if not need(d, "attribution_volatility"):
        return
    at = d["attribution_volatility"].set_index("risk_factor").reindex(FACTOR_ORDER).dropna(subset=["weight"]).reset_index()
    callout("The big idea",
            "Putting 45% of your money in something does not mean it causes 45% of your risk. Risk depends on how volatile an asset is "
            "and how it moves together with the rest. <b>Attribution</b> splits the portfolio's total risk into each asset's share.", "info")
    names = [factor_name(f) for f in at["risk_factor"]]
    fig = go.Figure()
    fig.add_bar(x=names, y=at["weight"] * 100, name="Share of money invested", marker_color=SLATE,
                text=[f"{v:.0f}%" for v in at["weight"] * 100], textposition="outside")
    fig.add_bar(x=names, y=at["pct_of_portfolio_variance"] * 100, name="Share of total risk", marker_color=[RED if v > 0 else GREEN for v in at["pct_of_portfolio_variance"]],
                text=[f"{v:.1f}%" for v in at["pct_of_portfolio_variance"] * 100], textposition="outside")
    fig.update_layout(barmode="group", title="Money vs. risk: who is over- and under-weight?", yaxis_title="%")
    plot(style_fig(fig, 430), key="at_bar")

    top = at.sort_values("pct_of_portfolio_variance", ascending=False).iloc[0]
    neg = at[at["pct_of_portfolio_variance"] < 0]
    msg = (f"<b>{factor_name(top['risk_factor'])}</b> is {top['weight']:.0%} of the money but <b>{top['pct_of_portfolio_variance']:.0%}</b> of the risk. ")
    if not neg.empty:
        msg += (f"<b>{factor_name(neg.iloc[0]['risk_factor'])}</b> has a negative share ({neg.iloc[0]['pct_of_portfolio_variance']:.1%}): "
                "it tends to move the opposite way, so owning it slightly <i>reduces</i> total risk - a natural hedge.")
    callout("What this tells us", msg, "good")

    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure(go.Pie(labels=names, values=at["pct_of_portfolio_variance"].clip(lower=0), hole=.55,
                               marker=dict(colors=[INDIGO, TEAL, AMBER, PINK, SKY]), textinfo="label+percent"))
        fig.update_layout(title="Share of portfolio risk (positive contributors)")
        plot(style_fig(fig, 380, legend=False), key="at_donut")
    with c2:
        rk = d["attribution_scenario_ranking"]
        if not rk.empty:
            rk = rk.sort_values("avg_abs_contribution")
            fig = go.Figure(go.Bar(y=[factor_name(f) for f in rk["risk_factor"]], x=rk["avg_abs_contribution"] * 100, orientation="h",
                                   marker_color=INDIGO, text=[f"{v:.2f}%" for v in rk["avg_abs_contribution"] * 100], textposition="outside"))
            fig.update_layout(title="Average impact across the 4 stress scenarios", xaxis_title="Average |P&L contribution| (% of portfolio)")
            plot(style_fig(fig, 380, legend=False), key="at_rank")
    with st.expander("See the full attribution table"):
        table(d["attribution_volatility"])
    st.caption("Method: Euler decomposition of portfolio variance - each asset's share = weight × marginal contribution, and the shares add up to 100%.")


# ----------------------------------------------------------------------------
# PAGE: Credit
# ----------------------------------------------------------------------------
def roc_points(y: np.ndarray, score: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    order = np.argsort(-score, kind="mergesort")
    y = y[order]
    tps, fps = np.cumsum(y), np.cumsum(1 - y)
    return np.r_[0, fps / max(fps[-1], 1)], np.r_[0, tps / max(tps[-1], 1)]


def page_credit(d: dict, cfg: dict) -> None:
    header("🏦", "Credit Risk", "How many borrowers will fail to repay - and what will it cost?")
    if not need(d, "credit_expected_loss", "credit_model_metrics"):
        return
    el, cm = d["credit_expected_loss"], d["credit_model_metrics"].set_index("model_id")
    allrow = el[el["segment"] == "ALL"].iloc[0]
    lgd = float(cfg.get("credit", {}).get("lgd_baseline", 0.45))

    md('<div class="formula">Expected Loss &nbsp;=&nbsp; PD &nbsp;×&nbsp; LGD &nbsp;×&nbsp; EAD</div>')
    a, b, c, e = st.columns(4)
    with a:
        kpi("PD · Probability of Default", pct(allrow["mean_pd"], 1), "Chance a borrower stops paying (predicted by ML)", INDIGO)
    with b:
        kpi("LGD · Loss Given Default", pct(lgd, 0), "Share of the loan that can't be recovered", AMBER)
    with c:
        kpi("EAD · Exposure at Default", usd(allrow["ead"]), "Total amount lent across all loans", SKY)
    with e:
        kpi("Expected Loss", usd(allrow["expected_loss"]), f"{pct(allrow['expected_loss_rate'], 1)} of everything lent", RED)

    t1, t2, t3, t4 = st.tabs(["🧱 Where the loss sits", "🤖 Which model is better?", "🎯 Are the probabilities honest?", "🌩️ Credit stress"])
    with t1:
        seg = el[el["segment"] != "ALL"].copy()
        order = ["small", "medium", "large"]
        seg["segment"] = pd.Categorical(seg["segment"], order, ordered=True)
        seg = seg.sort_values("segment")
        c1, c2 = st.columns(2)
        with c1:
            fig = go.Figure()
            fig.add_bar(x=seg["segment"].astype(str).str.title(), y=seg["ead"], name="Amount lent (EAD)", marker_color=SKY)
            fig.add_bar(x=seg["segment"].astype(str).str.title(), y=seg["expected_loss"], name="Expected loss", marker_color=RED)
            fig.update_layout(barmode="group", title="Money lent vs. money expected to be lost ($)", yaxis_tickprefix="$")
            plot(style_fig(fig, 380), key="cr_seg")
        with c2:
            fig = go.Figure(go.Bar(x=seg["segment"].astype(str).str.title(), y=seg["expected_loss_rate"] * 100,
                                   marker_color=[GREEN, AMBER, RED], text=[f"{v:.1%}" for v in seg["expected_loss_rate"]], textposition="outside"))
            fig.update_layout(title="Expected-loss rate by loan size (%)", yaxis_title="% of amount lent")
            plot(style_fig(fig, 380, legend=False), key="cr_rate")
        sp = d["credit_segment_performance"]
        if not sp.empty:
            sp = sp.copy()
            sp["segment"] = pd.Categorical(sp["segment"], order, ordered=True)
            sp = sp.sort_values("segment")
            fig = go.Figure()
            fig.add_bar(x=sp["segment"].astype(str).str.title(), y=sp["mean_predicted_pd"] * 100, name="Predicted default rate", marker_color=INDIGO)
            fig.add_bar(x=sp["segment"].astype(str).str.title(), y=sp["observed_default_rate"] * 100, name="Actual default rate", marker_color=PINK)
            fig.update_layout(barmode="group", title="Predicted vs. actual default rate by segment (%)")
            plot(style_fig(fig, 340), key="cr_segperf")
        big = seg.sort_values("expected_loss", ascending=False).iloc[0]
        callout("What this tells us",
                f"The <b>{str(big['segment'])}</b> loans carry {big['expected_loss'] / seg['expected_loss'].sum():.0%} of expected loss "
                f"with {big['ead'] / seg['ead'].sum():.0%} of the money lent - they are the riskiest per dollar "
                f"({pct(big['expected_loss_rate'], 1)} expected loss rate).", "warn")

    with t2:
        callout("How to read these scores",
                "<b>AUC</b>: pick one defaulter and one good borrower - how often does the model rank the defaulter as riskier? (0.5 = coin flip, 1 = perfect)<br>"
                "<b>KS</b>: how far apart the model pushes good and bad borrowers (higher = better separation)<br>"
                "<b>Brier score</b>: how accurate the predicted <i>probabilities</i> are (<b>lower</b> = better)", "info")
        cols = st.columns(2)
        for col, m in zip(cols, ["logistic_pd", "xgboost_pd"]):
            with col:
                r = cm.loc[m]
                md(f'<div class="card" style="border-top:4px solid {MODEL_COLOR[m]}"><h4>{model_name(m)}'
                   f'{" (baseline)" if m == "logistic_pd" else " (challenger)"}</h4>'
                   f'<p>AUC <b>{r["roc_auc"]:.3f}</b> &nbsp;·&nbsp; KS <b>{r["ks"]:.3f}</b> &nbsp;·&nbsp; Brier <b>{r["brier_score"]:.3f}</b></p></div>')
        pr = d["credit_predictions"]
        if not pr.empty:
            y = pr["default_flag"].to_numpy().astype(int)
            fig = go.Figure()
            for m in ["logistic_pd", "xgboost_pd"]:
                fpr, tpr = roc_points(y, pr[f"pd_{m}"].to_numpy())
                fig.add_scatter(x=fpr, y=tpr, mode="lines", name=f"{model_name(m)} (AUC {cm.loc[m, 'roc_auc']:.3f})",
                                line=dict(color=MODEL_COLOR[m], width=3))
            fig.add_scatter(x=[0, 1], y=[0, 1], mode="lines", name="Random guess", line=dict(color=SLATE, dash="dash"))
            fig.update_layout(title=f"ROC curve on {len(pr):,} unseen loans (closer to top-left = better)",
                              xaxis_title="False alarms (good borrowers flagged)", yaxis_title="Defaulters caught")
            plot(style_fig(fig, 430), key="cr_roc")
        st.caption("Models were tested on later-dated loans only (chronological split) so they could not 'peek' at the future.")

    with t3:
        worse = cm["brier_score"].idxmax()
        better = cm["brier_score"].idxmin()
        callout("Good ranking ≠ good probabilities",
                f"{model_name(worse)} predicts an average default rate of <b>{pct(cm.loc[worse, 'mean_predicted_pd'], 0)}</b> when the real rate is "
                f"<b>{pct(cm.loc[worse, 'observed_default_rate'], 1)}</b>, so its Brier score is {cm.loc[worse, 'brier_score'] / cm.loc[better, 'brier_score']:.1f}× worse "
                f"({cm.loc[worse, 'brier_score']:.3f} vs {cm.loc[better, 'brier_score']:.3f}). "
                f"Because Expected Loss needs <i>accurate probabilities</i>, {model_name(better)} is used for the loss calculation.", "warn")
        cal = d["credit_calibration"]
        if not cal.empty:
            fig = go.Figure()
            fig.add_scatter(x=[0, 1], y=[0, 1], mode="lines", name="Perfect calibration", line=dict(color=SLATE, dash="dash"))
            for m in ["logistic_pd", "xgboost_pd"]:
                g = cal[cal["model_id"] == m]
                fig.add_scatter(x=g["mean_predicted_pd"], y=g["observed_default_rate"], mode="lines+markers",
                                name=model_name(m), line=dict(color=MODEL_COLOR[m], width=3), marker=dict(size=9))
            fig.update_layout(title="Calibration: when the model says X%, how often do borrowers really default?",
                              xaxis_title="Predicted default probability", yaxis_title="Actual default rate",
                              xaxis_tickformat=".0%", yaxis_tickformat=".0%")
            fig.update_xaxes(range=[0, 0.85])
            fig.update_yaxes(range=[0, 0.85])
            plot(style_fig(fig, 460), key="cr_cal")
            st.caption("Points on the dashed diagonal = honest probabilities. Curves below it over-predict defaults; curves above it under-predict.")

    with t4:
        cs = d["credit_stress"]
        if not cs.empty:
            pm = cs[cs["segment"] == "ALL"].set_index("scenario_id")
            desc = "; ".join(f"<b>{i.title()}</b> = PD ×{r.pd_multiplier:g} &amp; LGD +{r.lgd_shift * 100:.0f} pts"
                             for i, r in pm.iterrows() if i != "BASELINE")
            callout("Recession simulator",
                    "Each scenario multiplies the default probabilities (PD) and raises the share lost when a borrower defaults (LGD): " + desc + ".", "info")
            ordr = ["BASELINE", "MODERATE", "SEVERE"]
            tot = cs[cs["segment"] == "ALL"].set_index("scenario_id").reindex(ordr)
            c = st.columns(3)
            for col, sid, colr in zip(c, ordr, [GREEN, AMBER, RED]):
                with col:
                    kpi(sid.title(), usd(tot.loc[sid, "expected_loss"]), f"{pct(tot.loc[sid, 'expected_loss_rate'], 1)} of exposure", colr)
            seg = cs[cs["segment"] != "ALL"]
            fig = go.Figure()
            for sg, colr in zip(["small", "medium", "large"], [SKY, INDIGO, PINK]):
                g = seg[seg["segment"] == sg].set_index("scenario_id").reindex(ordr)
                fig.add_bar(x=[s.title() for s in ordr], y=g["expected_loss"], name=sg.title(), marker_color=colr)
            fig.update_layout(barmode="stack", title="Expected credit loss by scenario ($)", yaxis_tickprefix="$")
            for s_, v in zip(ordr, tot["expected_loss"]):
                fig.add_annotation(x=s_.title(), y=v, text=usd(v), showarrow=False, yshift=14, font=dict(size=14))
            plot(style_fig(fig, 430), key="cr_stress")
            up = tot.loc["SEVERE", "expected_loss"] / tot.loc["BASELINE", "expected_loss"] - 1
            callout("Takeaway", f"In a severe recession expected losses rise by <b>{up:.0%}</b>"
                    f"{' - more than double - ' if up > 1 else ' '}even though the number of loans is unchanged.", "bad")
    dq = d["credit_data_quality"]
    if not dq.empty:
        with st.expander(f"🧼 Data-quality checks ({int(dq['passed'].sum())}/{len(dq)} passed)"):
            table(dq)
    st.caption("Credit data is synthetic (for offline reproducibility) - it is not a real loan portfolio.")


# ----------------------------------------------------------------------------
# PAGE: Governance
# ----------------------------------------------------------------------------
SEV_COLOR = {"HIGH": RED, "MEDIUM": AMBER, "LOW": SKY}


def page_governance(d: dict, cfg: dict) -> None:
    header("🛡️", "Governance & Validation", "Are we inside our limits, and can we trust our own models?")
    callout("Why this matters",
            "In a real bank, building a model is only half the job. Someone must also prove it is monitored, documented, "
            "within limits, and that its numbers reconcile. This page is that control layer.", "info")

    lim = d["risk_limits"]
    if not lim.empty:
        section("🚦 Risk limits", "Each dial shows how much of the allowed limit is used. Past 100% = breach.")
        labels = {"var_99": "99% VaR", "es_99": "99% Expected Shortfall", "stress_loss": "Stress loss", "credit_expected_loss": "Credit expected loss"}
        cols = st.columns(len(lim))
        for col, (_, r) in zip(cols, lim.iterrows()):
            u = float(r["utilization"]) * 100
            bar = RED if r["status"] == "BREACH" else (AMBER if u >= 80 else GREEN)
            fig = go.Figure(go.Indicator(
                mode="gauge+number", value=u, number=dict(suffix="%", valueformat=".0f"),
                title=dict(text=labels.get(r["metric"], r["metric"]), font=dict(size=15)),
                gauge=dict(axis=dict(range=[0, 200]), bar=dict(color=bar),
                           steps=[dict(range=[0, 80], color="rgba(34,197,94,.18)"), dict(range=[80, 100], color="rgba(245,158,11,.22)"),
                                  dict(range=[100, 200], color="rgba(239,68,68,.22)")],
                           threshold=dict(line=dict(color="white", width=3), thickness=.8, value=100))))
            fig.update_layout(height=250, margin=dict(l=20, r=20, t=60, b=10))
            with col:
                plot(fig, key=f"gov_g_{r['metric']}")
                st.caption(f"{pct(r['value'])} used vs. limit {pct(r['limit'])} → **{r['status']}**")
        breaches = lim[lim["status"] == "BREACH"]
        if not breaches.empty:
            callout("Limit breach detected",
                    "; ".join(f"<b>{labels.get(m, m)}</b> at {u:.0%} of its limit" for m, u in zip(breaches["metric"], breaches["utilization"])) +
                    ". Anything above 100% would be escalated to risk management.", "bad")

    fd = d["validation_findings"]
    if not fd.empty:
        section("📝 Validation findings", "Issues raised automatically by the validation engine, with evidence and a recommended action.")
        cols = st.columns(2)
        for i, (_, r) in enumerate(fd.sort_values("severity", key=lambda s: s.map({"HIGH": 0, "MEDIUM": 1, "LOW": 2})).iterrows()):
            with cols[i % 2]:
                md(f'<div class="card" style="border-left:5px solid {SEV_COLOR.get(r["severity"], INDIGO)}">'
                   f'<h4><span class="badge" style="--c:{SEV_COLOR.get(r["severity"], INDIGO)}">{r["severity"]}</span>'
                   f'{str(r["finding_id"]).replace("_", " ").title()}</h4>'
                   f'<p><b>Evidence:</b> {r["evidence"]}</p><p><b>Action:</b> {r["recommendation"]}</p>'
                   f'<p><b>Status:</b> {r["status"]}</p></div>')

    dr = d["drift_metrics"]
    if not dr.empty:
        section("🌊 Has the data changed? (drift monitoring)",
                "PSI (Population Stability Index) compares today's data with the data the model was built on. Under 0.10 = stable, 0.10-0.25 = watch, over 0.25 = significant shift.")
        mon = cfg.get("monitoring", {})
        w, b = float(mon.get("warning_threshold", .10)), float(mon.get("breach_threshold", .25))
        colmap = {"OK": GREEN, "WARNING": AMBER, "BREACH": RED}
        names = [factor_name(f) if f in FACTOR_LABEL else str(f).replace("_", " ").title() for f in dr["feature"]]
        fig = go.Figure(go.Bar(x=names, y=dr["psi"], marker_color=[colmap.get(s, INDIGO) for s in dr["status"]],
                               text=[f"{v:.3f}" for v in dr["psi"]], textposition="outside"))
        fig.add_hline(y=w, line_dash="dash", line_color=AMBER, annotation_text="Watch", annotation_position="top left")
        fig.add_hline(y=b, line_dash="dash", line_color=RED, annotation_text="Significant shift", annotation_position="top left")
        fig.update_layout(title="Drift score (PSI) per input", yaxis_title="PSI", yaxis_range=[0, max(b * 1.15, float(dr["psi"].max()) * 1.2)])
        plot(style_fig(fig, 380, legend=False), key="gov_psi")

    inv = d["model_inventory"]
    if not inv.empty:
        section("📚 Model inventory", "Every model is registered with its purpose, assumptions and known weaknesses - like a nutrition label.")
        cols = st.columns(3)
        for i, (_, r) in enumerate(inv.iterrows()):
            colr = GREEN if r["validation_status"] == "VALIDATED" else AMBER
            with cols[i % 3]:
                md(f'<div class="card"><h4>{model_name(r["model_id"])} <span class="badge" style="--c:{colr}">{r["validation_status"]}</span></h4>'
                   f'<p><b>Role:</b> {r["purpose"]}</p><p><b>Assumes:</b> {r["assumptions"]}</p>'
                   f'<p><b>Weakness:</b> {r["limitations"]}</p><p style="opacity:.6">v{r["version"]}</p></div>')

    rec = d["sql_reconciliation"]
    if not rec.empty:
        section("🔗 Python ↔ SQL reconciliation", "Results saved in the SQL database are re-added by SQL and compared with Python's own numbers.")
        cols = st.columns(len(rec))
        for col, (_, r) in zip(cols, rec.iterrows()):
            with col:
                ok = bool(r["passed"])
                kpi(str(r["check"]).replace("_", " ").capitalize(), "✅ Match" if ok else "❌ Mismatch",
                    f"Python {r['python_value']:,.2f} · SQL {r['sql_value']:,.2f}", GREEN if ok else RED)
    with st.expander("🗄️ Peek into the live SQL database"):
        try:
            from riskforge.database import RiskRepository, database_url
            repo = RiskRepository(database_url(cfg))
            repo.ensure_schema()
            sql_latest = repo.latest_risk_results(cfg["portfolio"]["id"])
            if sql_latest.empty:
                st.info("The database is reachable but contains no rows yet.")
            else:
                table(sql_latest)
        except Exception as exc:
            st.info(f"SQL layer not available in this environment ({type(exc).__name__}). The pipeline saves results to SQLite/PostgreSQL when it runs.")


# ----------------------------------------------------------------------------
# PAGE: About
# ----------------------------------------------------------------------------
def page_about(d: dict, cfg: dict) -> None:
    header("📖", "About & Methodology", "What was used, how it works, and what it does not claim.")
    c1, c2 = st.columns([2, 1])
    with c1:
        callout("Scope", "RiskSphere is an <b>educational, industry-style</b> portfolio project. It is <b>not</b> a production bank engine, "
                "a regulatory-capital calculator, or a claim of Basel / IFRS 9 / CECL compliance.", "warn")
    with c2:

        st.link_button("🚀 Live app", LIVE)

    section("🧰 Tech stack")
    stack = {
        "Language": ["Python 3.11+"],
        "Numerics & statistics": ["NumPy", "pandas", "SciPy", "statsmodels"],
        "Machine learning": ["scikit-learn", "XGBoost"],
        "Data": ["yfinance (optional)", "synthetic generator"],
        "Storage": ["SQLAlchemy", "SQLite", "PostgreSQL"],
        "Visualisation": ["Streamlit", "Plotly", "Matplotlib"],
        "Quality": ["pytest (49 tests)", "GitHub Actions CI", "YAML config"],
    }
    for k, v in stack.items():
        md(f"<b>{k}</b>&nbsp; " + "".join(f'<span class="chip">{x}</span>' for x in v))

    section("🔬 Methodology")
    t1, t2, t3, t4 = st.tabs(["Market risk", "Credit risk", "Stress & attribution", "Validation & governance"])
    with t1:
        st.markdown("""
**Four VaR models** forecast the 1-day, 99% loss using a rolling window of 250 days. Every forecast is strictly *out-of-sample* (uses only past data).

| Model | Idea | Weakness |
|---|---|---|
| Historical | Take the 1% worst day from the past 250 | Slow to react; the past may not include a crash |
| Parametric | Assume a bell-curve with measured volatility | Understates fat tails |
| EWMA | Bell-curve, but recent days count more (λ = 0.94) | Still assumes a bell-curve |
| GARCH(1,1) | Volatility itself evolves over time | Parameters fitted once on the initial window |

**Expected Shortfall** is the average loss beyond VaR. Interest-rate risk uses duration (7 yrs) and convexity (55).
""")
        st.latex(r"\mathrm{VaR}_{99\%}: \; P(\text{loss} > \mathrm{VaR}) = 1\% \qquad \mathrm{ES}_{99\%} = E[\text{loss} \mid \text{loss} > \mathrm{VaR}]")
        st.latex(r"\sigma_t^2 = \omega + \alpha\,\varepsilon_{t-1}^2 + \beta\,\sigma_{t-1}^2")
    with t2:
        st.markdown("""
- **PD (probability of default):** Logistic Regression (transparent baseline) vs. XGBoost (challenger), chronological train/test split to avoid look-ahead.
- **LGD & EAD:** simplified baselines (LGD = 45%, EAD = loan balance).
- **Expected Loss:** PD × LGD × EAD per loan, summed per segment.
- **Validation:** ROC-AUC, KS, Brier score, calibration curve, leakage scan, segment performance.
- **Credit stress:** scales PD and shifts LGD for Moderate / Severe scenarios.
""")
        st.latex(r"\mathrm{EL} = \mathrm{PD} \times \mathrm{LGD} \times \mathrm{EAD}")
    with t3:
        st.markdown("""
- **Scenario stress:** four configured scenarios shock all 5 risk factors; P&L = Σ weight × mapped return.
- **Reverse stress:** minimise the size (L2 norm) of the shock vector subject to *portfolio loss = 10%* and per-asset bounds, using multi-start optimisation.
- **Attribution:** Euler decomposition of portfolio variance into component contributions that sum to 100%.
""")
        st.latex(r"\text{Risk share}_i = \frac{w_i \,(\Sigma w)_i}{w^\top \Sigma\, w}")
    with t4:
        st.markdown("""
- **Backtesting:** Kupiec (breach count) and Christoffersen (breach independence) at 5% significance.
- **Drift:** Population Stability Index (10 bins) with warning at 0.10 and breach at 0.25.
- **Limits:** VaR, ES, stress loss and credit loss are compared with configured limits; breaches generate findings automatically.
- **Auditability:** data-version hash, model inventory, SQL persistence, Python ↔ SQL reconciliation.
""")

    section("⚠️ Honest limitations")
    st.markdown("""
- Market and credit data are **synthetic** (reproducible), not live institutional feeds.
- P&L is a **factor approximation**, not full repricing of every instrument.
- Duration/convexity ignores curve shape, credit spreads and optionality.
- Credit default definition, LGD and EAD are simplified.
- PSI thresholds and risk limits are illustrative heuristics, not regulatory standards.
""")
    md("<br><div class='card'><h4>👤 Built by Arin Bhardwaj</h4>"
       "<p>M.Sc. Mathematics &amp; Scientific Computing, NIT Warangal · Aspiring Data Scientist / ML Engineer</p></div>")


# ----------------------------------------------------------------------------
# App shell
# ----------------------------------------------------------------------------
P_HOME, P_MKT, P_BT, P_ST = "🏠 Start Here", "📉 Market Risk", "✅ Backtesting", "💥 Stress Testing"
P_ATTR, P_CR, P_GOV, P_ABOUT = "🧩 Risk Attribution", "🏦 Credit Risk", "🛡️ Governance", "📖 About & Method"
PAGES = {P_HOME: page_home, P_MKT: page_market, P_BT: page_backtest, P_ST: page_stress,
         P_ATTR: page_attribution, P_CR: page_credit, P_GOV: page_governance, P_ABOUT: page_about}


def main() -> None:
    st.set_page_config(page_title="RiskSphere | Financial Risk Analytics", page_icon="◈", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    cfg = load_cfg()
    d = {name: load_table(name).copy() for name in TABLES}

    if "nav" not in st.session_state:
        st.session_state["nav"] = P_HOME
    with st.sidebar:
        st.markdown("## ◈ RiskSphere")
        st.caption("Financial Risk & Quantitative Analytics Platform")
        st.radio("Navigate", list(PAGES), key="nav", label_visibility="collapsed")
        st.divider()
        st.caption("📌 New here? Start with **🏠 Start Here** - it explains everything in 2 minutes.")
        st.caption("Educational portfolio project · synthetic data · not regulatory software.")

    if all(df.empty for df in d.values()):
        st.error("No result files found. Run `python scripts/run_pipeline.py` from the repository root first.")
        return
    PAGES[st.session_state["nav"]](d, cfg)


if __name__ == "__main__":
    main()