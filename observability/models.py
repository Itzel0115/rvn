from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

TRACE_SCHEMA_VERSION = "revenue-poc-trace.v1"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class TraceEvent:
    event_name: str
    timestamp: str = field(default_factory=utc_now)
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class SpanRecord:
    trace_id: str
    span_id: str
    parent_span_id: str | None
    span_name: str
    span_kind: str = "internal"
    started_at: str = field(default_factory=utc_now)
    finished_at: str | None = None
    duration_ms: float | None = None
    status: str = "unset"
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[TraceEvent] = field(default_factory=list)
    links: list[dict[str, str]] = field(default_factory=list)
    error_type: str | None = None
    error_message_safe: str | None = None
    failure_category: str | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self); value["events"] = [asdict(event) for event in self.events]; return value


@dataclass
class ModelCallSummary:
    provider: str; model: str | None; operation: str
    input_token_count: int | None = None; output_token_count: int | None = None; total_token_count: int | None = None
    token_count_source: str = "unavailable"; duration_ms: float | None = None; status: str = "unknown"; retry_count: int = 0
    cost_amount: float | None = None; cost_currency: str | None = None; cost_status: str = "local_or_unavailable"


@dataclass
class TraceRun:
    trace_id: str; root_span_id: str; request_id: str | None; operation_name: str
    schema_version: str = TRACE_SCHEMA_VERSION
    thread_id: str | None = None; event_id: str | None = None; candidate_id: str | None = None; investigation_id: str | None = None
    runtime_mode: str | None = None; status: str = "running"; started_at: str = field(default_factory=utc_now); finished_at: str | None = None; duration_ms: float | None = None
    service_name: str = "revenue-poc"; service_version: str = "0.1.0"; working_tree_state: str = "unknown"; code_version_reference: str | None = None
    semantic_catalog_version: str | None = None; tool_registry_version: str | None = None; policy_versions: dict[str, str] = field(default_factory=dict); data_fixture_version: str | None = None; model_configuration_hash: str | None = None
    span_count: int = 0; tool_call_count: int = 0; model_call_count: int = 0; replan_count: int = 0
    final_status: str | None = None; stop_reason: str | None = None; failure_category: str | None = None
    content_capture_enabled: bool = False; redaction_policy_version: str = "redaction.v1"; evaluation_links: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]: return asdict(self)
    def to_json(self) -> str: return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, allow_nan=False)
