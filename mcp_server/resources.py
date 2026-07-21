from __future__ import annotations

from typing import Any

from semantic_layer import get_catalog
from tool_registry import TOOL_REGISTRY
from .security import sanitize_output

def read_resource(uri: str, freshness: dict[str, Any] | None = None) -> dict[str, Any]:
    catalog = get_catalog()
    if uri == "semantic://catalog/summary":
        return {"version": catalog.catalog_version(), "metric_count": len(catalog.list_metrics()), "dimension_count": len(catalog.list_dimensions()), "task_count": len(catalog.list_task_requirements()), "data_contract_count": len(catalog.list_data_contracts())}
    if uri == "semantic://metrics": return {"metrics": [x.to_dict() for x in catalog.list_metrics()]}
    if uri.startswith("semantic://metrics/"):
        metric = catalog.resolve_metric(uri.rsplit("/", 1)[1])
        if not metric: raise KeyError("resource_not_found")
        return metric.to_dict()
    if uri == "semantic://dimensions": return {"dimensions": [x.to_dict() for x in catalog.list_dimensions()]}
    if uri.startswith("semantic://dimensions/"):
        value = catalog.resolve_dimension(uri.rsplit("/", 1)[1])
        if not value: raise KeyError("resource_not_found")
        return value.to_dict()
    if uri.startswith("semantic://tasks/"):
        value = catalog.describe_task_requirements(uri.rsplit("/", 1)[1])
        if not value: raise KeyError("resource_not_found")
        return value
    if uri == "semantic://tools":
        return {"tools": [public_tool_contract(x) for x in TOOL_REGISTRY.values() if x.mcp_exposable and x.read_only and x.risk_level == "low"]}
    if uri == "semantic://data-contracts": return {"datasets": [x.to_dict() for x in catalog.list_data_contracts()]}
    if uri == "semantic://data-freshness":
        safe = {k: v for k, v in (freshness or {"status": "context_not_loaded"}).items() if k not in {"source_files", "rows", "raw_rows"}}
        return sanitize_output(safe)
    raise KeyError("resource_not_found")

def public_tool_contract(contract: Any) -> dict[str, Any]:
    return {"mcp_name": contract.mcp_name or contract.tool_name, "internal_tool_name": contract.tool_name, "description": contract.description, "input_schema": contract.input_schema, "supported_metrics": list(contract.supported_metric_ids or contract.supported_metrics), "supported_dimensions": list(contract.supported_dimension_ids or contract.supported_entity_dimensions), "supported_task_types": list(contract.allowed_task_families), "output_evidence_types": list(contract.output_evidence_types or ((contract.output_evidence_type,) if contract.output_evidence_type else ())), "evidence_roles": list(contract.evidence_roles), "row_limit": min(contract.max_output_rows, 20), "known_limitations": list(contract.known_limitations)}
