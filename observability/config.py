from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ObservabilityConfig:
    enabled: bool = False
    capture_content: bool = False
    store_backend: str = "sqlite"
    sample_rate: float = 1.0
    max_attribute_length: int = 512
    max_event_count: int = 50
    retention_days: int = 30
    database_path: Path = Path(os.getenv("TRACE_STORE_PATH", "output/observability/traces.sqlite3"))


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    if raw.strip().lower() in {"1", "true", "yes", "on"}:
        return True
    if raw.strip().lower() in {"0", "false", "no", "off"}:
        return False
    return default


def _int(name: str, default: int, minimum: int) -> int:
    try:
        return max(minimum, int(os.getenv(name, str(default))))
    except ValueError:
        return default


def get_config() -> ObservabilityConfig:
    try:
        sample_rate = float(os.getenv("TRACE_SAMPLE_RATE", "1.0"))
    except ValueError:
        sample_rate = 1.0
    return ObservabilityConfig(
        enabled=_bool("OBSERVABILITY_ENABLED", False),
        capture_content=_bool("TRACE_CAPTURE_CONTENT", False),
        store_backend=os.getenv("TRACE_STORE_BACKEND", "sqlite").strip().lower(),
        sample_rate=min(1.0, max(0.0, sample_rate)),
        max_attribute_length=_int("TRACE_MAX_ATTRIBUTE_LENGTH", 512, 64),
        max_event_count=_int("TRACE_MAX_EVENT_COUNT", 50, 1),
        retention_days=_int("TRACE_RETENTION_DAYS", 30, 1),
        database_path=Path(os.getenv("TRACE_STORE_PATH", "output/observability/traces.sqlite3")),
    )
