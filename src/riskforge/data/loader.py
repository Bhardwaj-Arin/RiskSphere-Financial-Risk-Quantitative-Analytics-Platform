"""Source-driven market-data ingestion with explicit provenance."""
from __future__ import annotations

from dataclasses import dataclass, asdict
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

from . import synthetic

REPO_ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = REPO_ROOT / "data" / "raw"
ARTIFACT_DIR = REPO_ROOT / "artifacts"


@dataclass
class DataProvenance:
    source: str
    retrieved_at: str
    start_date: str | None
    end_date: str | None
    row_count: int
    risk_factors: list[str]
    data_version: str
    factor_metadata: dict[str, Any]
    raw_path: str | None = None


def _utc_now() -> str:
    return pd.Timestamp.now(tz="UTC").isoformat()


def _data_version(df: pd.DataFrame) -> str:
    cols = [c for c in ["date", "risk_factor", "value", "source"] if c in df.columns]
    stable = df[cols].copy()
    if "date" in stable:
        stable["date"] = pd.to_datetime(stable["date"]).astype(str)
    payload = stable.sort_values(cols[:2]).to_csv(index=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def load_from_synthetic(start_date: str, end_date: str, factors: list[str] | None = None,
                        seed: int = 42) -> pd.DataFrame:
    return synthetic.generate_market_prices(start_date, end_date, factors, seed)


def load_from_yfinance(tickers: dict[str, str], start_date: str, end_date: str) -> pd.DataFrame:
    try:
        import yfinance as yf
    except ImportError as e:
        raise ImportError("yfinance is not installed. Run: pip install yfinance") from e

    frames: list[pd.DataFrame] = []
    retrieved_at = pd.Timestamp.now(tz="UTC")
    for factor, ticker in tickers.items():
        data = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=False)
        if data.empty:
            raise ValueError(f"No data returned for {ticker} ({factor})")
        close = data["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        s = close.rename("value").reset_index()
        date_col = s.columns[0]
        s = s.rename(columns={date_col: "date"})
        # ^TNX is conventionally quoted as yield percent (e.g., 4.25). Convert
        # to decimal yield so absolute changes match the synthetic convention.
        if factor == "RATES_10Y" and s["value"].median() > 1.0:
            s["value"] = s["value"] / 100.0
        s["risk_factor"] = factor
        s["source"] = f"yfinance:{ticker}"
        s["retrieved_at"] = retrieved_at
        frames.append(s[["date", "risk_factor", "value", "source", "retrieved_at"]])
    return pd.concat(frames, ignore_index=True).sort_values(["risk_factor", "date"]).reset_index(drop=True)


def load_from_csv(path: str | Path, source_label: str = "csv_import") -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    required = {"date", "risk_factor", "value"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing required columns: {sorted(missing)}")
    df = df.copy()
    df["source"] = source_label
    df["retrieved_at"] = pd.Timestamp.now(tz="UTC")
    return df.sort_values(["risk_factor", "date"]).reset_index(drop=True)


def load_market_data(config: dict[str, Any]) -> tuple[pd.DataFrame, DataProvenance]:
    dcfg = config["data"]
    source = str(dcfg.get("source", "synthetic")).lower()
    factors = list(dcfg["risk_factors"])
    start_date, end_date = dcfg.get("start_date"), dcfg.get("end_date")

    if source == "synthetic":
        df = load_from_synthetic(start_date, end_date, factors, int(dcfg.get("seed", 42)))
    elif source == "csv":
        path = dcfg.get("csv_path")
        if not path:
            raise ValueError("data.csv_path is required when data.source=csv")
        df = load_from_csv(REPO_ROOT / path if not Path(path).is_absolute() else path)
    elif source == "yfinance":
        tickers = dcfg.get("tickers", {})
        missing = set(factors) - set(tickers)
        if missing:
            raise ValueError(f"Missing yfinance tickers for: {sorted(missing)}")
        df = load_from_yfinance({f: tickers[f] for f in factors}, start_date, end_date)
    else:
        raise ValueError(f"Unsupported data.source={source!r}")

    actual_factors = sorted(df["risk_factor"].astype(str).unique().tolist())
    expected = sorted(factors)
    if actual_factors != expected:
        raise ValueError(f"Risk-factor schema mismatch. Expected {expected}, got {actual_factors}")

    prov = DataProvenance(
        source=source,
        retrieved_at=_utc_now(),
        start_date=str(pd.to_datetime(df["date"]).min().date()),
        end_date=str(pd.to_datetime(df["date"]).max().date()),
        row_count=len(df),
        risk_factors=actual_factors,
        data_version=_data_version(df),
        factor_metadata=dcfg.get("factor_metadata", {}),
    )
    return df, prov


def save_raw(df: pd.DataFrame, filename: str | None = None) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if filename is None:
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"market_prices_{stamp}.csv"
    out_path = RAW_DIR / filename
    if out_path.exists():
        raise FileExistsError(f"Raw data file already exists: {out_path}")
    df.to_csv(out_path, index=False)
    return out_path


def save_provenance(provenance: DataProvenance, raw_path: Path | None = None) -> Path:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    payload = asdict(provenance)
    payload["raw_path"] = str(raw_path.relative_to(REPO_ROOT)) if raw_path else None
    out = ARTIFACT_DIR / "data_provenance.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out
