from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


ENTITY_LABELS = {
    "overall": "整體",
    "business_group": "事業群",
    "product_line_5": "產品線",
    "platform": "平台",
}

METRIC_LABELS = {
    "revenue": "營收",
    "revenue_amount": "營收",
    "inventory_amount": "庫存金額",
    "inventory_qty": "庫存數量",
    "revenue_inventory_amount_ratio": "營收相對庫存效率 proxy",
    "health_score": "health_score",
    "risk_score": "risk_score",
}

PERIOD_PAIR_TOOLS = {"get_period_pair_metric_comparison", "get_entity_period_pair_comparison"}
CHART_TOOLS = {"get_chart_payload", "get_chart_table", "create_chart_image"}
DATA_QUALITY_TOOLS = {"get_data_coverage", "get_mapping_summary", "get_tool_capability_matrix"}


@dataclass(frozen=True)
class EvidenceContract:
    evidence_id: str
    evidence_type: str
    source_tool: str
    task_family: str
    time_scope: dict[str, Any]
    entity_scope: dict[str, Any]
    metric: str | None
    metric_label: str | None
    rows: list[dict[str, Any]] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    limitations: list[str] = field(default_factory=list)
    data_quality_flags: list[str] = field(default_factory=list)
    raw_reference: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def validate_basic(self) -> tuple[bool, list[str]]:
        errors: list[str] = []
        if not self.evidence_id:
            errors.append("missing_evidence_id")
        if not self.evidence_type:
            errors.append("missing_evidence_type")
        if not self.source_tool:
            errors.append("missing_source_tool")
        if not self.task_family:
            errors.append("missing_task_family")
        metric_optional = self.evidence_type in {"data_quality", "unsupported_tool_output"}
        if not metric_optional and not self.metric:
            errors.append("missing_metric")
        if not isinstance(self.rows, list):
            errors.append("rows_not_list")
        if not isinstance(self.limitations, list):
            errors.append("limitations_not_list")
        return not errors, errors

    @classmethod
    def from_tool_output(
        cls,
        tool_name: str,
        output: Any,
        canonical_task_profile: Any,
        *,
        evidence_index: int = 0,
    ) -> "EvidenceContract":
        return EvidenceContractBuilder().normalize_tool_output(
            tool_name,
            output,
            canonical_task_profile,
            evidence_index=evidence_index,
        )

    @staticmethod
    def normalize_tool_output(tool_name: str, output: Any, canonical_task_profile: Any) -> "EvidenceContract":
        return EvidenceContract.from_tool_output(tool_name, output, canonical_task_profile)


class EvidenceContractBuilder:
    def build_evidence_contracts(self, tool_results: Any, canonical_task_profile: Any) -> list[EvidenceContract]:
        outputs = list(_iter_tool_outputs(tool_results))
        contracts: list[EvidenceContract] = []
        for index, (tool_name, output) in enumerate(outputs, start=1):
            contracts.append(
                self.normalize_tool_output(
                    tool_name,
                    output,
                    canonical_task_profile,
                    evidence_index=index,
                )
            )
        return contracts

    def normalize_tool_output(
        self,
        tool_name: str,
        output: Any,
        canonical_task_profile: Any,
        *,
        evidence_index: int = 0,
    ) -> EvidenceContract:
        output_tool = _source_tool(tool_name, output)
        output_type = _evidence_type(output)
        if output_type == "chart_payload" or output_tool in CHART_TOOLS:
            return self._normalize_chart_payload(output_tool, output, canonical_task_profile, evidence_index)
        if output_tool == "get_entity_month_table":
            if _task_family(canonical_task_profile) == "cross_section_compare":
                return self._normalize_cross_section_comparison(output_tool, output, canonical_task_profile, evidence_index)
            return self._normalize_entity_month_table(output_tool, output, canonical_task_profile, evidence_index)
        if output_tool == "get_entity_period_pair_table":
            return self._normalize_entity_period_pair_table(output_tool, output, canonical_task_profile, evidence_index)
        if output_tool == "get_entity_multi_month_table":
            return self._normalize_entity_multi_month_table(output_tool, output, canonical_task_profile, evidence_index)
        if output_tool == "get_entity_metric_value" or output_type == "entity_metric_lookup":
            return self._normalize_entity_metric_lookup(output_tool, output, canonical_task_profile, evidence_index)
        if output_tool == "get_entity_metric_ranking":
            return self._normalize_entity_metric_ranking(output_tool, output, canonical_task_profile, evidence_index)
        if output_tool == "get_entity_time_series":
            return self._normalize_entity_time_series(output_tool, output, canonical_task_profile, evidence_index)
        if output_tool == "get_overall_time_series":
            return self._normalize_overall_time_series(output_tool, output, canonical_task_profile, evidence_index)
        if output_tool in PERIOD_PAIR_TOOLS:
            return self._normalize_period_pair_comparison(output_tool, output, canonical_task_profile, evidence_index)
        if output_tool == "get_entity_cross_section_comparison":
            return self._normalize_cross_section_comparison(output_tool, output, canonical_task_profile, evidence_index)
        if output_tool == "get_entity_performance_snapshot" or output_type == "parent_child_drilldown":
            return self._normalize_entity_performance_snapshot(output_tool, output, canonical_task_profile, evidence_index)
        if output_tool == "get_revenue_inventory_relationship":
            return self._normalize_relationship_analysis(output_tool, output, canonical_task_profile, evidence_index)
        if output_tool == "get_entity_contribution_analysis":
            return self._normalize_contribution_analysis(output_tool, output, canonical_task_profile, evidence_index)
        if output_tool in DATA_QUALITY_TOOLS:
            return self._normalize_data_quality(output_tool, output, canonical_task_profile, evidence_index)
        return self._unsupported_tool_output(output_tool, output, canonical_task_profile, evidence_index)

    def _normalize_entity_month_table(self, tool_name: str, output: Any, profile: Any, index: int) -> EvidenceContract:
        return self._contract("entity_month_table", tool_name, output, profile, index)

    def _normalize_entity_period_pair_table(self, tool_name: str, output: Any, profile: Any, index: int) -> EvidenceContract:
        return self._contract("entity_period_pair_table", tool_name, output, profile, index)

    def _normalize_entity_multi_month_table(self, tool_name: str, output: Any, profile: Any, index: int) -> EvidenceContract:
        return self._contract("entity_multi_month_table", tool_name, output, profile, index)

    def _normalize_entity_metric_lookup(self, tool_name: str, output: Any, profile: Any, index: int) -> EvidenceContract:
        rows = _rows(output)
        if not rows and isinstance(output, dict):
            rows = [{
                "entity_value": output.get("entity_value"),
                "month": output.get("month"),
                "metric": _metric(output, profile),
                "value": output.get("value"),
            }]
        return self._contract("entity_metric_lookup", tool_name, output, profile, index, rows=rows)

    def _normalize_entity_metric_ranking(self, tool_name: str, output: Any, profile: Any, index: int) -> EvidenceContract:
        return self._contract("entity_metric_ranking", tool_name, output, profile, index)

    def _normalize_entity_time_series(self, tool_name: str, output: Any, profile: Any, index: int) -> EvidenceContract:
        return self._contract("entity_time_series", tool_name, output, profile, index)

    def _normalize_overall_time_series(self, tool_name: str, output: Any, profile: Any, index: int) -> EvidenceContract:
        return self._contract("overall_time_series", tool_name, output, profile, index)

    def _normalize_period_pair_comparison(self, tool_name: str, output: Any, profile: Any, index: int) -> EvidenceContract:
        rows = _rows(output)
        if not rows and isinstance(output, dict):
            rows = list(output.get("breakdown") or [])
        summary = dict(output.get("summary") or {}) if isinstance(output, dict) else {}
        if isinstance(output, dict) and output.get("overall"):
            summary = {**summary, "overall": output.get("overall")}
        return self._contract("period_pair_comparison", tool_name, output, profile, index, rows=rows, summary=summary)

    def _normalize_cross_section_comparison(self, tool_name: str, output: Any, profile: Any, index: int) -> EvidenceContract:
        return self._contract("cross_section_comparison", tool_name, output, profile, index)

    def _normalize_entity_performance_snapshot(self, tool_name: str, output: Any, profile: Any, index: int) -> EvidenceContract:
        return self._contract("entity_performance_snapshot", tool_name, output, profile, index)

    def _normalize_relationship_analysis(self, tool_name: str, output: Any, profile: Any, index: int) -> EvidenceContract:
        return self._contract("relationship_analysis", tool_name, output, profile, index)

    def _normalize_contribution_analysis(self, tool_name: str, output: Any, profile: Any, index: int) -> EvidenceContract:
        return self._contract("contribution_analysis", tool_name, output, profile, index)

    def _normalize_chart_payload(self, tool_name: str, output: Any, profile: Any, index: int) -> EvidenceContract:
        rows = _rows(output)
        summary: dict[str, Any] = {}
        if isinstance(output, dict):
            rows = rows or list(output.get("table_preview") or [])
            summary = {
                "chart_key": output.get("chart_key"),
                "chart_type": output.get("chart_type"),
                "title": output.get("title"),
                "series_count": len(output.get("series") or []),
                "label_count": len(output.get("labels") or []),
            }
        elif isinstance(output, list):
            rows = list(output)
        return self._contract("chart_payload", tool_name, output, profile, index, rows=rows, summary=summary)

    def _normalize_data_quality(self, tool_name: str, output: Any, profile: Any, index: int) -> EvidenceContract:
        rows = _rows(output)
        summary = dict(output) if isinstance(output, dict) else {}
        return self._contract("data_quality", tool_name, output, profile, index, rows=rows, summary=summary, metric=None)

    def _unsupported_tool_output(self, tool_name: str, output: Any, profile: Any, index: int) -> EvidenceContract:
        return self._contract(
            "unsupported_tool_output",
            tool_name,
            output,
            profile,
            index,
            rows=_rows(output),
            limitations=[f"EvidenceContractBuilder does not yet support tool output: {tool_name}"],
            metric=None,
        )

    def _contract(
        self,
        evidence_type: str,
        tool_name: str,
        output: Any,
        profile: Any,
        index: int,
        *,
        rows: list[dict[str, Any]] | None = None,
        summary: dict[str, Any] | None = None,
        limitations: list[str] | None = None,
        metric: str | None | object = ...,
    ) -> EvidenceContract:
        output_dict = output if isinstance(output, dict) else {}
        resolved_metric = _metric(output_dict, profile) if metric is ... else metric
        metric_label = _metric_label(output_dict, resolved_metric)
        return EvidenceContract(
            evidence_id=_evidence_id(tool_name, evidence_type, index),
            evidence_type=evidence_type,
            source_tool=tool_name,
            task_family=_task_family(profile),
            time_scope=_time_scope(output_dict, profile),
            entity_scope=_entity_scope(output_dict, profile),
            metric=resolved_metric,
            metric_label=metric_label,
            rows=list(rows if rows is not None else _rows(output)),
            summary=dict(summary if summary is not None else _summary(output)),
            limitations=list(dict.fromkeys([*(limitations or []), *_limitations(output)])),
            data_quality_flags=_data_quality_flags(output),
            raw_reference=_raw_reference(output),
        )


def from_tool_output(tool_name: str, output: Any, canonical_task_profile: Any) -> EvidenceContract:
    return EvidenceContract.from_tool_output(tool_name, output, canonical_task_profile)


def normalize_tool_output(tool_name: str, output: Any, canonical_task_profile: Any) -> EvidenceContract:
    return EvidenceContract.normalize_tool_output(tool_name, output, canonical_task_profile)


def build_evidence_contracts(tool_results: Any, canonical_task_profile: Any) -> list[EvidenceContract]:
    return EvidenceContractBuilder().build_evidence_contracts(tool_results, canonical_task_profile)


def _iter_tool_outputs(tool_results: Any):
    if tool_results is None:
        return
    if isinstance(tool_results, dict):
        if "evidence" in tool_results and isinstance(tool_results.get("evidence"), list):
            for item in tool_results.get("evidence") or []:
                yield _source_tool("unknown", item), item
            return
        yield _source_tool("unknown", tool_results), tool_results
        return
    if not isinstance(tool_results, list):
        evidence = getattr(tool_results, "evidence", None)
        if isinstance(evidence, list):
            for item in evidence:
                yield _source_tool("unknown", item), item
        return
    for result in tool_results:
        if isinstance(result, dict) and isinstance(result.get("evidence"), list):
            for item in result.get("evidence") or []:
                yield _source_tool("unknown", item), item
        else:
            evidence = getattr(result, "evidence", None)
            if isinstance(evidence, list):
                for item in evidence:
                    yield _source_tool("unknown", item), item
            elif isinstance(result, dict):
                yield _source_tool("unknown", result), result


def _source_tool(fallback: str, output: Any) -> str:
    if isinstance(output, dict):
        return str(output.get("source_tool") or output.get("tool_name") or fallback or "unknown")
    return str(fallback or "unknown")


def _evidence_type(output: Any) -> str | None:
    return str(output.get("evidence_type")) if isinstance(output, dict) and output.get("evidence_type") else None


def _task_family(profile: Any) -> str:
    return str(_get(profile, "task_family") or "")


def _time_scope(output: dict[str, Any], profile: Any) -> dict[str, Any]:
    canonical = dict(_get(profile, "time_scope") or {})
    return {
        "mode": canonical.get("mode") or output.get("mode"),
        "month": canonical.get("month") or canonical.get("single_month") or output.get("month") or _filters_month(output),
        "period_a": canonical.get("period_a") or output.get("period_a"),
        "period_b": canonical.get("period_b") or output.get("period_b"),
        "start_month": canonical.get("start_month") or output.get("start_month"),
        "end_month": canonical.get("end_month") or output.get("end_month"),
        "recent_n": canonical.get("recent_n") or output.get("recent_n"),
    }


def _entity_scope(output: dict[str, Any], profile: Any) -> dict[str, Any]:
    target = dict(_get(profile, "target_entity") or {})
    parent = dict(_get(profile, "parent_entity") or {})
    parent_filter = output.get("parent_filter") if isinstance(output.get("parent_filter"), dict) else {}
    dimension = target.get("dimension") or output.get("entity_dimension") or output.get("dimension") or "overall"
    value = target.get("value") if target.get("value") is not None else output.get("entity_value")
    parent_dimension = parent.get("dimension") or ("business_group" if parent_filter.get("business_group") else None)
    parent_value = parent.get("value") if parent.get("value") is not None else parent_filter.get("business_group")
    return {
        "dimension": dimension,
        "label": output.get("entity_label") or ENTITY_LABELS.get(str(dimension), str(dimension)),
        "scope": target.get("scope") or ("single" if value else "overall" if dimension == "overall" else "unspecified"),
        "value": value,
        "parent_dimension": parent_dimension,
        "parent_value": parent_value,
    }


def _metric(output: dict[str, Any], profile: Any) -> str | None:
    canonical = _get(profile, "metric")
    if canonical:
        return str(canonical)
    metric = output.get("metric")
    if metric == "revenue":
        return "revenue_amount"
    return str(metric) if metric is not None else None


def _metric_label(output: dict[str, Any], metric: str | None) -> str | None:
    return output.get("metric_label") or METRIC_LABELS.get(str(metric), metric)


def _rows(output: Any) -> list[dict[str, Any]]:
    if isinstance(output, list):
        return [dict(item) for item in output if isinstance(item, dict)]
    if isinstance(output, dict) and isinstance(output.get("rows"), list):
        return [dict(item) for item in output.get("rows") or [] if isinstance(item, dict)]
    return []


def _summary(output: Any) -> dict[str, Any]:
    if isinstance(output, dict) and isinstance(output.get("summary"), dict):
        return dict(output.get("summary") or {})
    return {}


def _limitations(output: Any) -> list[str]:
    if isinstance(output, dict) and isinstance(output.get("limitations"), list):
        return [str(item) for item in output.get("limitations") or [] if item]
    return []


def _data_quality_flags(output: Any) -> list[str]:
    flags: list[str] = []
    for row in _rows(output):
        flag = row.get("data_presence_flag")
        if flag:
            flags.append(str(flag))
    if isinstance(output, dict):
        for key in ["data_presence_flag", "quality_flag"]:
            if output.get(key):
                flags.append(str(output[key]))
    return list(dict.fromkeys(flags))


def _raw_reference(output: Any) -> dict[str, Any] | None:
    if not isinstance(output, dict):
        return None
    reference_keys = ["chart_key", "chart_type", "source_tool", "evidence_type", "filters"]
    return {key: output.get(key) for key in reference_keys if key in output}


def _filters_month(output: dict[str, Any]) -> Any:
    filters = output.get("filters")
    if isinstance(filters, dict):
        return filters.get("month")
    return None


def _evidence_id(tool_name: str, evidence_type: str, index: int) -> str:
    safe_tool = str(tool_name or "unknown").replace(" ", "_")
    return f"ev-{index:03d}-{safe_tool}-{evidence_type}"


def _get(value: Any, name: str) -> Any:
    if isinstance(value, dict):
        return value.get(name)
    return getattr(value, name, None)
