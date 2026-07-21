from __future__ import annotations

import math
import re
from typing import Any

from tool_registry import TOOL_REGISTRY

MAX_ROWS = 20
MONTH = re.compile(r"^\d{4}-\d{2}")

def is_read_only_tool(tool_name: str) -> bool:
    item = TOOL_REGISTRY.get(tool_name)
    return bool(item and item.read_only)

def is_mcp_exposable(tool_name: str) -> bool:
    item = TOOL_REGISTRY.get(tool_name)
    return bool(item and item.mcp_exposable and item.read_only and item.risk_level == "low")

def validate_tool_arguments(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(arguments, dict) or not is_mcp_exposable(tool_name): raise ValueError("tool_not_exposed")
    contract = TOOL_REGISTRY[tool_name]
    unknown = set(arguments) - set(contract.allowed_args)
    if unknown: raise ValueError("unsupported_arguments")
    missing = [name for name in contract.required_args if arguments.get(name) in {None, ""}]
    if missing: raise ValueError("missing_required_arguments")
    result = dict(arguments)
    for key in ("month", "period_a", "period_b", "start_month", "end_month"):
        if key in result and result[key] is not None and not MONTH.match(str(result[key])): raise ValueError("invalid_period")
    if result.get("start_month") and result.get("end_month") and result["start_month"] > result["end_month"]: raise ValueError("invalid_period_range")
    if result.get("period_a") and result.get("period_b") and result["period_a"] == result["period_b"]: raise ValueError("invalid_period_pair")
    if "metric" in result and contract.supported_metrics and result["metric"] not in contract.supported_metrics: raise ValueError("invalid_metric")
    if "entity_dimension" in result and contract.supported_entity_dimensions and result["entity_dimension"] not in contract.supported_entity_dimensions: raise ValueError("invalid_dimension")
    if "top_n" in result and (not isinstance(result["top_n"], int) or not 1 <= result["top_n"] <= MAX_ROWS): raise ValueError("invalid_top_n")
    for value in result.values():
        if isinstance(value, str) and ("/" in value or "\\" in value or ".." in value): raise ValueError("unsafe_argument")
    return result

def sanitize_output(value: Any, *, depth: int = 0) -> Any:
    if value is None or isinstance(value, (str, int, bool)): return "<redacted-path>" if isinstance(value, str) and value.startswith("/") else value
    if isinstance(value, float): return value if math.isfinite(value) else None
    if depth >= 5: return "<truncated>"
    if isinstance(value, dict): return {str(k): sanitize_output(v, depth=depth + 1) for k, v in list(value.items())[:40] if str(k) not in {"source_files", "traceback"}}
    if isinstance(value, (list, tuple)): return [sanitize_output(v, depth=depth + 1) for v in value[:MAX_ROWS]]
    if hasattr(value, "item"): return sanitize_output(value.item(), depth=depth + 1)
    return str(value)

def enforce_row_limit(result: Any) -> Any: return sanitize_output(result)
