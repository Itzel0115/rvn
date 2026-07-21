from __future__ import annotations

import hashlib
import json
from typing import Any

from semantic_layer import get_catalog

def build_dataset_fingerprint(context: Any, semantic_catalog: Any | None = None) -> dict[str, Any]:
    catalog = semantic_catalog or get_catalog()
    datasets = []
    for dataset_id, frame in (("revenue_logical", context.revenue_df), ("inventory_logical", context.inventory_df)):
        columns = sorted(map(str, frame.columns))
        period_column = "month_key" if "month_key" in frame.columns else "month"
        periods = sorted(str(item) for item in frame[period_column].dropna().unique()) if period_column in frame.columns else []
        numeric = [column for column in frame.columns if column in {"revenue_amount", "inventory_amount", "inventory_qty", "revenue", "inventory"}]
        aggregates = {column: round(float(frame[column].fillna(0).sum()), 6) for column in numeric}
        datasets.append({"dataset_id": dataset_id, "row_count": int(len(frame)), "columns": columns, "period_start": periods[0] if periods else None, "period_end": periods[-1] if periods else None, "aggregates": aggregates})
    payload = {"algorithm": "logical-metadata-sha256.v1", "catalog_version": catalog.catalog_version(), "datasets": datasets}
    payload["fingerprint"] = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    return payload

def compare_fingerprints(previous: dict[str, Any] | None, current: dict[str, Any]) -> dict[str, Any]:
    changed = previous is None or previous.get("fingerprint") != current.get("fingerprint")
    return {"changed": changed, "previous": previous.get("fingerprint") if previous else None, "current": current.get("fingerprint"), "algorithm": current.get("algorithm")}
