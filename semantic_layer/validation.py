from __future__ import annotations

from typing import Any

from tool_registry import TOOL_REGISTRY
from task_profile import ACTIVE_CANONICAL_TASK_TYPES


def validate_catalog(catalog: Any) -> dict[str, list[str]]:
    errors: list[str] = []; warnings: list[str] = []; aliases: dict[str, str] = {}
    for metric in catalog.list_metrics():
        if metric.is_proxy and not metric.limitations: errors.append(f"proxy_missing_limitation:{metric.metric_id}")
        for dimension in metric.allowed_dimensions:
            if dimension not in {x.dimension_id for x in catalog.list_dimensions()}: errors.append(f"metric_missing_dimension:{metric.metric_id}:{dimension}")
        for tool in [*metric.primary_tools, *metric.supporting_tools]:
            if tool not in TOOL_REGISTRY: errors.append(f"metric_missing_tool:{metric.metric_id}:{tool}")
        for alias in [metric.metric_id, *metric.aliases]:
            key = alias.lower()
            if key in aliases and aliases[key] != metric.metric_id: errors.append(f"duplicate_metric_alias:{alias}")
            aliases[key] = metric.metric_id
    metrics = {x.metric_id for x in catalog.list_metrics()}; dimensions = {x.dimension_id for x in catalog.list_dimensions()}
    known_evidence_types = {contract.output_evidence_type for contract in TOOL_REGISTRY.values() if contract.output_evidence_type}
    for task in catalog.list_task_requirements():
        for tool in [*task.allowed_primary_tools, *task.allowed_supporting_tools, *task.forbidden_as_primary]:
            if tool not in TOOL_REGISTRY: errors.append(f"task_missing_tool:{task.task_type}:{tool}")
        if set(task.allowed_primary_tools) & set(task.forbidden_as_primary): errors.append(f"primary_forbidden_conflict:{task.task_type}")
        if set(task.allowed_primary_tools) & set(task.allowed_supporting_tools): errors.append(f"primary_supporting_conflict:{task.task_type}")
        for evidence_type in [*task.required_primary_evidence, *task.required_supporting_evidence, *task.optional_counter_evidence]:
            if evidence_type not in known_evidence_types: errors.append(f"task_missing_evidence_type:{task.task_type}:{evidence_type}")
        for metric in task.required_metrics:
            if metric not in metrics: errors.append(f"task_missing_metric:{task.task_type}:{metric}")
        for dimension in task.required_dimensions:
            if dimension not in dimensions: errors.append(f"task_missing_dimension:{task.task_type}:{dimension}")
    glossary_aliases: dict[str, str] = {}
    for term in catalog.list_glossary():
        for metric in term.related_metrics:
            if metric not in metrics: errors.append(f"glossary_missing_metric:{term.term_id}:{metric}")
        for dimension in term.related_dimensions:
            if dimension not in dimensions: errors.append(f"glossary_missing_dimension:{term.term_id}:{dimension}")
        for alias in [term.canonical_term, *term.aliases]:
            key = alias.lower()
            if key in glossary_aliases and glossary_aliases[key] != term.term_id: errors.append(f"duplicate_glossary_alias:{alias}")
            glossary_aliases[key] = term.term_id
    for contract in catalog.list_data_contracts():
        if not contract.required_columns or not contract.period_field or not contract.numeric_fields:
            errors.append(f"invalid_data_contract:{contract.dataset_id}")
    evidence_types = {task_type for task_type in ()}
    mcp_names: set[str] = set()
    for contract in TOOL_REGISTRY.values():
        if contract.max_output_rows <= 0: errors.append(f"invalid_row_cap:{contract.tool_name}")
        for metric_id in contract.supported_metric_ids:
            if metric_id not in metrics: errors.append(f"tool_missing_metric:{contract.tool_name}:{metric_id}")
        for dimension_id in contract.supported_dimension_ids:
            if dimension_id not in dimensions: errors.append(f"tool_missing_dimension:{contract.tool_name}:{dimension_id}")
        if contract.mcp_exposable:
            if not contract.read_only or contract.risk_level != "low": errors.append(f"unsafe_mcp_tool:{contract.tool_name}")
            name = contract.mcp_name or contract.tool_name
            if name in mcp_names: errors.append(f"duplicate_mcp_name:{name}")
            mcp_names.add(name)
            if not (contract.output_evidence_types or contract.output_evidence_type): errors.append(f"mcp_missing_evidence_type:{contract.tool_name}")
    coverage = {item.task_type: item for item in catalog.list_task_coverage()}
    for task_type in ACTIVE_CANONICAL_TASK_TYPES:
        if task_type not in coverage: errors.append(f"active_task_missing_coverage:{task_type}")
    for task_type in coverage:
        if task_type not in ACTIVE_CANONICAL_TASK_TYPES: warnings.append(f"coverage_task_not_active:{task_type}")
    for task in catalog.list_task_requirements():
        item = coverage.get(task.task_type)
        if item is None: errors.append(f"task_missing_coverage:{task.task_type}")
        elif item.runtime_path != "semantic": errors.append(f"semantic_task_not_semantic_path:{task.task_type}")
    for task_type, item in coverage.items():
        if item.runtime_path not in {"semantic", "legacy", "unsupported"}: errors.append(f"invalid_runtime_path:{task_type}")
        if item.coverage_status not in {"full", "partial", "intentional_legacy", "unsupported"}: errors.append(f"invalid_coverage_status:{task_type}")
        if not item.required_limitation: errors.append(f"coverage_missing_limitation:{task_type}")
    return {"errors": errors, "warnings": warnings}


if __name__ == "__main__":
    from .catalog import get_catalog
    catalog = get_catalog(); report = validate_catalog(catalog)
    print(f"Semantic catalog valid\nMetrics: {len(catalog.list_metrics())}\nDimensions: {len(catalog.list_dimensions())}\nTask evidence definitions: {len(catalog.list_task_requirements())}\nGlossary: {len(catalog.list_glossary())}\nData contracts: {len(catalog.list_data_contracts())}\nCoverage entries: {len(catalog.list_task_coverage())}\nWarnings: {len(report['warnings'])}\nErrors: {len(report['errors'])}")
    raise SystemExit(1 if report["errors"] else 0)
