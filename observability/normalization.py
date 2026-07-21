from __future__ import annotations
import hashlib
from typing import Any
from .redaction import hash_content

def normalize_trace(trace: dict[str, Any]) -> list[dict[str, Any]]:
    spans = trace.get("spans", []) if isinstance(trace, dict) else []
    normalized=[]
    for span in spans:
        attributes=span.get("attributes") or {}; operation=span.get("span_name") or span.get("operation")
        item={"operation": operation, "status": span.get("status"), "tool_name": attributes.get("revenue_poc.tool.name") or attributes.get("tool_name"), "args_fingerprint": attributes.get("args_fingerprint"), "evidence_types": attributes.get("revenue_poc.evidence.types"), "semantic_requirement": attributes.get("revenue_poc.semantic.requirement_id"), "stop_reason": attributes.get("revenue_poc.stop.reason")}
        normalized.append({k:v for k,v in item.items() if v not in (None, "", [])})
    if not normalized and isinstance(trace, dict):
        normalized.append({"operation": trace.get("operation_name", "agent.run"), "status": trace.get("status"), "stop_reason": trace.get("stop_reason")})
    return normalized

def trajectory_fingerprint(normalized: list[dict[str, Any]]) -> str:
    import json
    return hashlib.sha256(json.dumps(normalized, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
