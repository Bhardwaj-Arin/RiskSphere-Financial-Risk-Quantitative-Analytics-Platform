"""Simple period-by-period model stability summaries."""
from __future__ import annotations

import pandas as pd


def market_backtest_stability(backtest_tables: dict[str, pd.DataFrame], freq: str = "YE") -> pd.DataFrame:
    rows = []
    for model_id, table in backtest_tables.items():
        g = table.copy()
        g["forecast_date"] = pd.to_datetime(g["forecast_date"])
        g = g.set_index("forecast_date")
        for period_end, p in g.resample(freq):
            if p.empty:
                continue
            rows.append({
                "model_id": model_id,
                "period_end": period_end.date(),
                "n_forecasts": len(p),
                "n_exceptions": int(p["exception_flag"].sum()),
                "exception_rate": float(p["exception_flag"].mean()),
                "avg_var": float(p["var"].mean()),
                "realized_loss_std": float(p["realized_loss"].std(ddof=1)) if len(p) > 1 else 0.0,
            })
    return pd.DataFrame(rows)
