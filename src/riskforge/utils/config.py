"""Configuration loading and validation for RiskSphere."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIGS_DIR = REPO_ROOT / "configs"


@dataclass(frozen=True)
class RiskSettings:
    confidence: float
    horizon_days: int
    training_window: int


def load_config(name: str = "base.yaml") -> dict[str, Any]:
    path = CONFIGS_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if name == "base.yaml":
        validate_base_config(cfg)
    return cfg


def validate_base_config(config: dict[str, Any]) -> None:
    risk = config.get("risk", {})
    # Backward-compatibility guard: old repositories had both window=250 and
    # min_train_window=500. RiskSphere has one canonical training_window.
    if "window" in risk or "min_train_window" in risk:
        vals = [risk.get(k) for k in ("training_window", "window", "min_train_window") if risk.get(k) is not None]
        if len(set(vals)) > 1:
            raise ValueError(
                "Conflicting rolling-window settings detected. Use only risk.training_window."
            )
    confidence = float(risk["confidence"])
    if not 0.5 < confidence < 1.0:
        raise ValueError("risk.confidence must be between 0.5 and 1")
    if int(risk["training_window"]) < 30:
        raise ValueError("risk.training_window must be at least 30 observations")
    weights = config["portfolio"]["weights"]
    if abs(sum(float(x) for x in weights.values()) - 1.0) > 1e-8:
        raise ValueError("portfolio.weights must sum to 1.0")


def risk_settings(config: dict[str, Any]) -> RiskSettings:
    validate_base_config(config)
    risk = config["risk"]
    return RiskSettings(
        confidence=float(risk["confidence"]),
        horizon_days=int(risk.get("horizon_days", config.get("portfolio", {}).get("horizon_days", 1))),
        training_window=int(risk["training_window"]),
    )
