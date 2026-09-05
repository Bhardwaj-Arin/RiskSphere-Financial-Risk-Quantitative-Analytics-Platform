"""Post-pipeline smoke check for required RiskSphere artifacts."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
required = [
    "market_risk_results.csv", "statistical_tests.csv", "stress_scenarios.csv",
    "credit_expected_loss.csv", "risk_limits.csv", "model_inventory.csv",
    "sql_reconciliation.csv",
]
missing = [name for name in required if not (ROOT / "results" / "tables" / name).exists()]
if missing:
    raise SystemExit(f"Missing required pipeline outputs: {missing}")
rec = pd.read_csv(ROOT / "results" / "tables" / "sql_reconciliation.csv")
if not rec["passed"].astype(bool).all():
    raise SystemExit("SQL reconciliation smoke check failed")
print("RiskSphere smoke check: PASS")
