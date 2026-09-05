# Data Dictionary

## Market input

| Column | Meaning |
|---|---|
| `date` | Market observation date |
| `risk_factor` | Canonical factor name |
| `value` | Price/index/yield level |
| `source` | Synthetic, CSV, or provider label |
| `retrieved_at` | Retrieval timestamp |

## Unified market-risk result

| Column | Meaning |
|---|---|
| `model` | Model identifier |
| `confidence` | VaR/ES confidence |
| `horizon` | Forecast horizon in days |
| `VaR` | Positive loss threshold |
| `ES` | Positive tail expected loss |
| `forecast_date` | Date forecast applies to |
| `realized_return` | Realized portfolio return on forecast date |
| `exception` | Realized loss exceeded VaR |
| `training_window` | Number of observations in configured training window |
| `data_version` | Hash-based provenance identifier |

## Credit prediction result

| Column | Meaning |
|---|---|
| `default_flag` | Observed binary target in holdout |
| `pd` | Predicted probability of default used for EL view |
| `lgd` | Loss-given-default assumption |
| `ead` | Exposure-at-default amount/proxy |
| `expected_loss` | `pd × lgd × ead` |
| `segment` | Optional portfolio segment |

## Risk limit result

| Column | Meaning |
|---|---|
| `metric` | Controlled risk metric |
| `value` | Current value |
| `limit` | Configured threshold |
| `utilization` | `value / limit` |
| `status` | `OK`, `WARNING`, or `BREACH` |
