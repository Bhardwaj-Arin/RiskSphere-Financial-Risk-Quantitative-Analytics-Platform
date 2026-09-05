"""Structured JSON logging for reproducible pipeline runs."""
from __future__ import annotations

import json
import logging
from pathlib import Path
import datetime as dt

REPO_ROOT = Path(__file__).resolve().parents[3]


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "event"):
            payload["event"] = getattr(record, "event")
        return json.dumps(payload, default=str)


def configure_logging() -> logging.Logger:
    root = logging.getLogger()
    if root.handlers:
        return logging.getLogger("riskquant")
    root.setLevel(logging.INFO)
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    root.addHandler(console)
    out = REPO_ROOT / "artifacts" / "riskquant.log"
    out.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(out, encoding="utf-8")
    file_handler.setFormatter(JsonFormatter())
    root.addHandler(file_handler)
    return logging.getLogger("riskquant")
