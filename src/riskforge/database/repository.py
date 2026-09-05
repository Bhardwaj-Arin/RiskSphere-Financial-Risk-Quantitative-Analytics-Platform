"""SQLAlchemy repository for RiskQuant persistence.

PostgreSQL is the intended deployment database. For offline demonstration and
CI, the same repository supports a local SQLite fallback without changing
business logic.
"""
from __future__ import annotations

import datetime as dt
import os
from pathlib import Path
from typing import Any
import uuid

import numpy as np
import pandas as pd
from sqlalchemy import (
    MetaData, Table, Column, String, Integer, Float, Boolean, Date, DateTime,
    Text, create_engine, select, func, delete
)
from sqlalchemy.engine import Engine

REPO_ROOT = Path(__file__).resolve().parents[3]
metadata = MetaData()

model_runs = Table(
    "model_runs", metadata,
    Column("run_id", String(64), primary_key=True),
    Column("executed_at", DateTime, nullable=False),
    Column("model_version", String(32), nullable=False),
    Column("data_source", String(128), nullable=False),
    Column("data_version", String(64)),
    Column("git_commit", String(64)),
    Column("status", String(32), nullable=False),
)
market_prices = Table(
    "market_prices", metadata,
    Column("run_id", String(64), primary_key=True),
    Column("date", Date, primary_key=True),
    Column("risk_factor", String(64), primary_key=True),
    Column("value", Float, nullable=False),
    Column("source", String(128), nullable=False),
    Column("retrieved_at", DateTime),
)
portfolio_positions = Table(
    "portfolio_positions", metadata,
    Column("run_id", String(64), primary_key=True),
    Column("portfolio_id", String(64), primary_key=True),
    Column("risk_factor", String(64), primary_key=True),
    Column("weight", Float, nullable=False),
    Column("notional", Float, nullable=False),
)
risk_results = Table(
    "risk_results", metadata,
    Column("run_id", String(64), primary_key=True),
    Column("forecast_date", Date, primary_key=True),
    Column("portfolio_id", String(64), primary_key=True),
    Column("model_id", String(64), primary_key=True),
    Column("confidence", Float, nullable=False),
    Column("horizon", Integer, nullable=False),
    Column("var", Float, nullable=False),
    Column("expected_shortfall", Float),
    Column("realized_return", Float),
    Column("exception_flag", Boolean),
    Column("training_window", Integer),
    Column("data_version", String(64)),
)
backtest_results = Table(
    "backtest_results", metadata,
    Column("run_id", String(64), primary_key=True),
    Column("forecast_date", Date, primary_key=True),
    Column("model_id", String(64), primary_key=True),
    Column("var", Float, nullable=False),
    Column("realized_return", Float),
    Column("realized_loss", Float),
    Column("exception_flag", Boolean, nullable=False),
)
stress_results = Table(
    "stress_results", metadata,
    Column("run_id", String(64), primary_key=True),
    Column("scenario_id", String(64), primary_key=True),
    Column("risk_factor", String(64), primary_key=True),
    Column("shock", Float, nullable=False),
    Column("mapped_return_shock", Float),
    Column("factor_contribution", Float),
    Column("portfolio_loss", Float, nullable=False),
)
risk_attribution = Table(
    "risk_attribution", metadata,
    Column("run_id", String(64), primary_key=True),
    Column("risk_factor", String(64), primary_key=True),
    Column("weight", Float),
    Column("pct_of_portfolio_variance", Float),
    Column("component_volatility", Float),
)
credit_predictions = Table(
    "credit_predictions", metadata,
    Column("run_id", String(64), primary_key=True),
    Column("row_id", Integer, primary_key=True),
    Column("model_id", String(64), nullable=False),
    Column("pd", Float, nullable=False),
    Column("lgd", Float, nullable=False),
    Column("ead", Float, nullable=False),
    Column("expected_loss", Float, nullable=False),
    Column("default_flag", Integer),
    Column("segment", String(64)),
)
risk_limits = Table(
    "risk_limits", metadata,
    Column("run_id", String(64), primary_key=True),
    Column("metric", String(64), primary_key=True),
    Column("value", Float, nullable=False),
    Column("limit_value", Float, nullable=False),
    Column("utilization", Float, nullable=False),
    Column("status", String(32), nullable=False),
)
model_inventory = Table(
    "model_inventory", metadata,
    Column("run_id", String(64), primary_key=True),
    Column("model_id", String(64), primary_key=True),
    Column("purpose", String(256)),
    Column("target", String(256)),
    Column("data", String(128)),
    Column("training_period", String(128)),
    Column("features", Text),
    Column("assumptions", Text),
    Column("limitations", Text),
    Column("version", String(32)),
    Column("validation_status", String(32)),
)


def database_url(config: dict[str, Any]) -> str:
    return os.getenv("RISKQUANT_DATABASE_URL") or config.get("database", {}).get("fallback_url", "sqlite:///artifacts/riskquant.db")


def _python(v: Any) -> Any:
    if pd.isna(v):
        return None
    if isinstance(v, pd.Timestamp):
        return v.to_pydatetime()
    if isinstance(v, np.generic):
        return v.item()
    return v


class RiskRepository:
    def __init__(self, url: str):
        self.url = url
        if url.startswith("sqlite:///"):
            path = url.removeprefix("sqlite:///")
            p = Path(path)
            if not p.is_absolute():
                p = REPO_ROOT / p
                self.url = f"sqlite:///{p}"
            p.parent.mkdir(parents=True, exist_ok=True)
        self.engine: Engine = create_engine(self.url, future=True)

    @property
    def backend(self) -> str:
        return self.engine.dialect.name

    def ensure_schema(self) -> None:
        metadata.create_all(self.engine)

    def start_run(self, meta: dict[str, Any], data_version: str) -> str:
        run_id = f"rq_{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S')}_{uuid.uuid4().hex[:8]}"
        row = {
            "run_id": run_id,
            "executed_at": dt.datetime.now(dt.timezone.utc).replace(tzinfo=None),
            "model_version": str(meta.get("model_version", "unknown")),
            "data_source": str(meta.get("data_source", "unknown")),
            "data_version": data_version,
            "git_commit": str(meta.get("git_commit", "unknown")),
            "status": "RUNNING",
        }
        with self.engine.begin() as conn:
            conn.execute(model_runs.insert(), [row])
        return run_id

    def finish_run(self, run_id: str, status: str = "COMPLETED") -> None:
        with self.engine.begin() as conn:
            conn.execute(model_runs.update().where(model_runs.c.run_id == run_id).values(status=status))

    def persist_market_prices(self, run_id: str, df: pd.DataFrame) -> None:
        records = []
        for _, r in df.iterrows():
            retrieved = pd.to_datetime(r.get("retrieved_at"), errors="coerce")
            records.append({
                "run_id": run_id, "date": pd.to_datetime(r["date"]).date(),
                "risk_factor": str(r["risk_factor"]), "value": float(r["value"]),
                "source": str(r.get("source", "unknown")),
                "retrieved_at": None if pd.isna(retrieved) else retrieved.to_pydatetime().replace(tzinfo=None),
            })
        with self.engine.begin() as conn:
            conn.execute(market_prices.insert(), records)

    def persist_positions(self, run_id: str, portfolio_id: str, weights: dict[str, float], notional: float) -> None:
        rows = [{"run_id": run_id, "portfolio_id": portfolio_id, "risk_factor": f,
                 "weight": float(w), "notional": float(notional)} for f, w in weights.items()]
        with self.engine.begin() as conn:
            conn.execute(portfolio_positions.insert(), rows)

    def persist_risk_results(self, run_id: str, portfolio_id: str, df: pd.DataFrame) -> None:
        rows = [{
            "run_id": run_id, "forecast_date": pd.to_datetime(r["forecast_date"]).date(),
            "portfolio_id": portfolio_id, "model_id": str(r["model"]),
            "confidence": float(r["confidence"]), "horizon": int(r["horizon"]),
            "var": float(r["VaR"]), "expected_shortfall": float(r["ES"]),
            "realized_return": float(r["realized_return"]), "exception_flag": bool(r["exception"]),
            "training_window": int(r["training_window"]), "data_version": str(r["data_version"]),
        } for _, r in df.iterrows()]
        with self.engine.begin() as conn:
            conn.execute(risk_results.insert(), rows)

    def persist_backtests(self, run_id: str, tables: dict[str, pd.DataFrame]) -> None:
        rows = []
        for model_id, df in tables.items():
            for _, r in df.iterrows():
                rows.append({"run_id": run_id, "forecast_date": pd.to_datetime(r["forecast_date"]).date(),
                             "model_id": model_id, "var": float(r["var"]),
                             "realized_return": float(r["realized_return"]), "realized_loss": float(r["realized_loss"]),
                             "exception_flag": bool(r["exception_flag"])})
        with self.engine.begin() as conn:
            conn.execute(backtest_results.insert(), rows)

    def persist_stress(self, run_id: str, df: pd.DataFrame) -> None:
        rows = [{"run_id": run_id, "scenario_id": str(r["scenario_id"]), "risk_factor": str(r["risk_factor"]),
                 "shock": float(r["shock"]), "mapped_return_shock": float(r.get("mapped_return_shock", r["shock"])),
                 "factor_contribution": float(r["factor_contribution"]), "portfolio_loss": float(r["portfolio_loss"])}
                for _, r in df.iterrows()]
        with self.engine.begin() as conn:
            conn.execute(stress_results.insert(), rows)

    def persist_attribution(self, run_id: str, df: pd.DataFrame) -> None:
        rows = [{"run_id": run_id, "risk_factor": str(r["risk_factor"]), "weight": float(r["weight"]),
                 "pct_of_portfolio_variance": float(r["pct_of_portfolio_variance"]),
                 "component_volatility": float(r.get("component_volatility", 0.0))} for _, r in df.iterrows()]
        with self.engine.begin() as conn:
            conn.execute(risk_attribution.insert(), rows)

    def persist_credit(self, run_id: str, df: pd.DataFrame, model_id: str) -> None:
        rows = []
        for i, r in df.reset_index(drop=True).iterrows():
            rows.append({"run_id": run_id, "row_id": int(i), "model_id": model_id, "pd": float(r["pd"]),
                         "lgd": float(r["lgd"]), "ead": float(r["ead"]), "expected_loss": float(r["expected_loss"]),
                         "default_flag": int(r["default_flag"]) if "default_flag" in r and not pd.isna(r["default_flag"]) else None,
                         "segment": str(r["segment"]) if "segment" in r and not pd.isna(r["segment"]) else None})
        with self.engine.begin() as conn:
            conn.execute(credit_predictions.insert(), rows)

    def persist_limits(self, run_id: str, df: pd.DataFrame) -> None:
        rows = [{"run_id": run_id, "metric": str(r["metric"]), "value": float(r["value"]),
                 "limit_value": float(r["limit"]), "utilization": float(r["utilization"]), "status": str(r["status"])}
                for _, r in df.iterrows()]
        with self.engine.begin() as conn:
            conn.execute(risk_limits.insert(), rows)

    def persist_inventory(self, run_id: str, df: pd.DataFrame) -> None:
        rows = []
        for _, r in df.iterrows():
            rows.append({"run_id": run_id, **{c: (None if pd.isna(r.get(c)) else str(r.get(c))) for c in
                ["model_id", "purpose", "target", "data", "training_period", "features", "assumptions", "limitations", "version", "validation_status"]}})
        with self.engine.begin() as conn:
            conn.execute(model_inventory.insert(), rows)

    def latest_risk_results(self, portfolio_id: str) -> pd.DataFrame:
        with self.engine.connect() as conn:
            latest_run = conn.execute(
                select(model_runs.c.run_id).where(model_runs.c.status == "COMPLETED")
                .order_by(model_runs.c.executed_at.desc()).limit(1)
            ).scalar_one_or_none()
        if latest_run is None:
            return pd.DataFrame()
        rr = risk_results.alias("rr")
        sub = (select(rr.c.model_id, func.max(rr.c.forecast_date).label("max_date"))
               .where((rr.c.portfolio_id == portfolio_id) & (rr.c.run_id == latest_run))
               .group_by(rr.c.model_id).subquery())
        stmt = (select(rr).join(sub, (rr.c.model_id == sub.c.model_id) & (rr.c.forecast_date == sub.c.max_date))
                .where((rr.c.portfolio_id == portfolio_id) & (rr.c.run_id == latest_run))
                .order_by(rr.c.model_id))
        return pd.read_sql(stmt, self.engine)

    def reconciliation(self, run_id: str, in_memory_risk: pd.DataFrame,
                       in_memory_stress: pd.DataFrame) -> pd.DataFrame:
        rows = []
        with self.engine.connect() as conn:
            db_risk_count = conn.execute(select(func.count()).select_from(risk_results).where(risk_results.c.run_id == run_id)).scalar_one()
            db_risk_sum = conn.execute(select(func.sum(risk_results.c.var)).where(risk_results.c.run_id == run_id)).scalar_one() or 0.0
            db_stress_count = conn.execute(select(func.count()).select_from(stress_results).where(stress_results.c.run_id == run_id)).scalar_one()
            db_stress_sum = conn.execute(select(func.sum(stress_results.c.portfolio_loss)).where(stress_results.c.run_id == run_id)).scalar_one() or 0.0
        checks = [
            ("risk_row_count", len(in_memory_risk), int(db_risk_count), 0.0),
            ("risk_var_sum", float(in_memory_risk["VaR"].sum()), float(db_risk_sum), 1e-9),
            ("stress_row_count", len(in_memory_stress), int(db_stress_count), 0.0),
            ("stress_loss_sum", float(in_memory_stress["portfolio_loss"].sum()), float(db_stress_sum), 1e-9),
        ]
        for name, py_val, sql_val, tol in checks:
            diff = abs(float(py_val) - float(sql_val))
            rows.append({"check": name, "python_value": py_val, "sql_value": sql_val,
                         "absolute_difference": diff, "passed": diff <= tol})
        return pd.DataFrame(rows)
