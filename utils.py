from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass
class MessageCollector:
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    infos: list[str] = field(default_factory=list)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def add_error(self, message: str) -> None:
        self.errors.append(message)

    def add_info(self, message: str) -> None:
        self.infos.append(message)

    def extend(self, other: "MessageCollector") -> None:
        self.warnings.extend(other.warnings)
        self.errors.extend(other.errors)
        self.infos.extend(other.infos)


def ensure_directories(paths: list[Path]) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def safe_strip(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip()
    return value


def normalize_code(value: Any) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip().upper()
    return text or None


def dataframe_to_records(df: pd.DataFrame, limit: int = 10) -> list[dict[str, Any]]:
    if df.empty:
        return []
    subset = df.head(limit).copy()
    return subset.where(pd.notna(subset), None).to_dict(orient="records")


def format_number(value: Any, decimals: int = 2) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        return f"{value:,.{decimals}f}"
    return str(value)
