from __future__ import annotations

import json
import math
import re
from dataclasses import asdict, is_dataclass
from typing import Any


MONTH_PATTERN = re.compile(r"20\d{2}[-/]\d{1,2}")
NUMBER_PATTERN = re.compile(r"(?<![\w-])\d[\d,]*(?:\.\d+)?%?(?![\w-])")
INTERNAL_TOOL_PATTERN = re.compile(r"\bget_[a-zA-Z0-9_]+\b")
DEBUG_STRING_PATTERN = re.compile(r"\b(?:table\s+)?rows\s*=\s*\d+\b", re.IGNORECASE)

ROOT_CAUSE_PHRASES = [
    "原因就是",
    "已確認根本原因",
    "confirmed root cause",
    "because it caused",
    "導致",
]
FORECAST_CLAIMS = [
    "下個月會改善",
    "下月會改善",
    "會改善",
    "會成長",
    "will improve",
    "will grow",
    "is forecast to improve",
]
PROXY_METRICS = {"revenue_inventory_amount_ratio", "health_score", "risk_score"}
METRIC_LABELS = {
    "revenue_amount": ("營收", "revenue"),
    "inventory_amount": ("庫存", "庫存金額", "庫存水位", "inventory"),
    "inventory_qty": ("庫存數量", "庫存 QTY", "inventory qty"),
    "revenue_inventory_amount_ratio": ("營收相對庫存", "效率 proxy", "ratio"),
    "health_score": ("health_score", "health score", "健康分數"),
    "risk_score": ("risk_score", "risk score", "風險分數"),
    "gross_margin": ("毛利", "gross margin", "margin"),
}
MULTI_METRIC_TASK_FAMILIES = {
    "latest_month_entity_summary",
    "cross_section_compare",
    "performance_assessment",
    "metric_relationship_analysis",
    "parent_child_drilldown",
}
GENERIC_ENTITY_TOKENS = {
    "產品線",
    "各產品線",
    "五大產品線",
    "事業群",
    "各事業群",
    "新事業群",
    "各新事業群",
    "BU",
    "各BU",
}


class WriterValidator:
    def validate(
        self,
        canonical_task_profile: Any,
        evidence_contracts: list[Any],
        writer_output: dict[str, Any],
        deterministic_display_blocks: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        violations: list[str] = []
        text = _writer_text(writer_output)
        canonical = _to_plain_dict(canonical_task_profile)
        evidence_dicts = [_to_plain_dict(contract) for contract in evidence_contracts]
        allowed_months = _collect_months([canonical, *evidence_dicts])
        output_months = _collect_months([text])
        wrong_months = sorted(month for month in output_months if month not in allowed_months)
        if wrong_months:
            violations.append(f"month_not_in_evidence:{wrong_months}")

        allowed_numbers = _collect_allowed_numbers([canonical, *evidence_dicts])
        output_numbers = _extract_output_numbers(text)
        new_numbers = sorted(token for token in output_numbers if _normalize_number_token(token) not in allowed_numbers)
        if new_numbers:
            violations.append(f"number_not_in_evidence:{new_numbers}")

        entity_violations = _find_entity_violations(text, canonical, evidence_dicts)
        violations.extend(entity_violations)

        metric_violation = _find_metric_violation(_writer_metric_text(writer_output), canonical, evidence_dicts)
        if metric_violation:
            violations.append(metric_violation)

        task_family = str(canonical.get("task_family") or "")
        lowered = text.lower()
        if task_family == "forecast_unsupported" and any(phrase.lower() in lowered for phrase in FORECAST_CLAIMS):
            if not _is_safe_forecast_refusal(text):
                violations.append("forecast_violation:unsupported_forecast_claim")

        root_hits = [phrase for phrase in ROOT_CAUSE_PHRASES if phrase.lower() in lowered]
        if root_hits:
            violations.append(f"root_cause_violation:{root_hits}")

        proxy_violation = _find_proxy_violation(text, canonical, evidence_dicts)
        if proxy_violation:
            violations.append(proxy_violation)

        limitation_violation = _find_limitation_violation(writer_output, evidence_dicts, deterministic_display_blocks)
        if limitation_violation:
            violations.append(limitation_violation)

        internal_hits = sorted(set(INTERNAL_TOOL_PATTERN.findall(text)))
        if "source_tool" in text or internal_hits:
            violations.append(f"internal_tool_name_violation:{internal_hits or ['source_tool']}")
        if DEBUG_STRING_PATTERN.search(text) or "debug" in lowered:
            violations.append("debug_string_violation")

        valid = not violations
        return {
            "valid": valid,
            "violations": violations,
            "fallback_to_deterministic": not valid,
            "reason": "valid" if valid else violations[0],
        }


def validate_writer_output(
    canonical_task_profile: Any,
    evidence_contracts: list[Any],
    writer_output: dict[str, Any],
    deterministic_display_blocks: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return WriterValidator().validate(
        canonical_task_profile,
        evidence_contracts,
        writer_output,
        deterministic_display_blocks,
    )


def _writer_text(writer_output: dict[str, Any]) -> str:
    parts = [
        writer_output.get("headline"),
        writer_output.get("table_caption"),
        writer_output.get("confidence_note"),
    ]
    parts.extend(writer_output.get("key_observations") or [])
    parts.extend(writer_output.get("limitations") or [])
    return "\n".join(str(part) for part in parts if part is not None)


def _writer_metric_text(writer_output: dict[str, Any]) -> str:
    parts = [
        writer_output.get("headline"),
        writer_output.get("table_caption"),
    ]
    parts.extend(writer_output.get("key_observations") or [])
    return "\n".join(str(part) for part in parts if part is not None)


def _is_safe_forecast_refusal(text: str) -> bool:
    return any(token in text for token in ["無法判斷", "無法預測", "不能預測", "無法直接預測", "尚無法判斷"])


def _to_plain_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if is_dataclass(value):
        return asdict(value)
    return {}


def _collect_months(values: list[Any]) -> set[str]:
    months: set[str] = set()
    for item in _walk_values(values):
        if isinstance(item, str):
            for match in MONTH_PATTERN.findall(item):
                months.add(_normalize_month(match))
    return months


def _extract_output_numbers(text: str) -> list[str]:
    text_without_months = MONTH_PATTERN.sub(" ", text)
    return NUMBER_PATTERN.findall(text_without_months)


def _collect_allowed_numbers(values: list[Any]) -> set[str]:
    allowed: set[str] = set()
    for item in _walk_values(values):
        if isinstance(item, bool) or item is None:
            continue
        if isinstance(item, (int, float)) and math.isfinite(float(item)):
            allowed.update(_number_variants(float(item)))
        elif isinstance(item, str):
            for token in _extract_output_numbers(item):
                allowed.add(_normalize_number_token(token))
    return allowed


def _number_variants(value: float) -> set[str]:
    variants = {
        _normalize_number_token(str(value)),
        _normalize_number_token(f"{value:.0f}"),
        _normalize_number_token(f"{value:,.0f}"),
        _normalize_number_token(f"{value:.1f}"),
        _normalize_number_token(f"{value:,.1f}"),
        _normalize_number_token(f"{value:.2f}"),
        _normalize_number_token(f"{value:,.2f}"),
        _normalize_number_token(f"{value:.4f}"),
    }
    if -1.0 <= value <= 1.0 and value != 0:
        percent_value = value * 100
        variants.update(
            {
                _normalize_number_token(f"{percent_value:.0f}%"),
                _normalize_number_token(f"{percent_value:.1f}%"),
                _normalize_number_token(f"{percent_value:.2f}%"),
            }
        )
    if float(value).is_integer():
        variants.add(str(int(value)))
    return {variant for variant in variants if variant}


def _normalize_number_token(token: str) -> str:
    token = str(token).strip().replace(",", "")
    if token.endswith("%"):
        token = token[:-1]
    try:
        value = float(token)
    except ValueError:
        return token
    if value.is_integer():
        return str(int(value))
    return format(value, "f").rstrip("0").rstrip(".")


def _normalize_month(month: str) -> str:
    year, raw_month = re.split(r"[-/]", month)
    return f"{year}-{int(raw_month):02d}"


def _find_entity_violations(text: str, canonical: dict[str, Any], evidence_dicts: list[dict[str, Any]]) -> list[str]:
    allowed = _collect_entities(canonical, evidence_dicts)
    violations: list[str] = []
    for token in re.findall(r"[\w\u4e00-\u9fff]+(?:產品線|事業群)", text):
        if "或" in token or "部分資料列" in token:
            continue
        if token in GENERIC_ENTITY_TOKENS:
            continue
        base = token.removesuffix("產品線").removesuffix("事業群")
        if token not in allowed and base not in allowed:
            if not any(token in entity or entity in token for entity in allowed):
                violations.append(f"entity_not_in_evidence:{token}")
    return violations


def _collect_entities(canonical: dict[str, Any], evidence_dicts: list[dict[str, Any]]) -> set[str]:
    entities: set[str] = set()
    for container in [canonical, *evidence_dicts]:
        target = container.get("target_entity") or {}
        parent = container.get("parent_entity") or {}
        entity_scope = container.get("entity_scope") or {}
        for value in [
            target.get("value"),
            parent.get("value"),
            entity_scope.get("value"),
            entity_scope.get("parent_value"),
        ]:
            if value:
                entities.add(str(value))
        for row in container.get("rows") or []:
            if isinstance(row, dict):
                for key in ["entity_value", "entity", "name", "business_group", "product_line", "事業群", "產品線"]:
                    if row.get(key):
                        entities.add(str(row[key]))
    return entities


def _find_metric_violation(text: str, canonical: dict[str, Any], evidence_dicts: list[dict[str, Any]]) -> str | None:
    task_family = str(canonical.get("task_family") or "")
    if task_family == "forecast_unsupported":
        return None
    allowed_metrics = _collect_allowed_metrics(canonical, evidence_dicts)
    mentioned_metrics = _mentioned_metrics(text)
    if not mentioned_metrics:
        return None
    canonical_metric = str(canonical.get("metric") or "")
    is_multi_metric = task_family in MULTI_METRIC_TASK_FAMILIES or len(allowed_metrics) > 1
    if not is_multi_metric and canonical_metric:
        allowed_metrics = {canonical_metric}
    unsupported = sorted(metric for metric in mentioned_metrics if not _metric_allowed(metric, allowed_metrics))
    if unsupported:
        return f"metric_violation:metric_not_in_evidence:{unsupported}"
    return None


def _collect_allowed_metrics(canonical: dict[str, Any], evidence_dicts: list[dict[str, Any]]) -> set[str]:
    metrics: set[str] = set()
    if canonical.get("metric"):
        metrics.add(str(canonical["metric"]))
    for contract in evidence_dicts:
        if contract.get("metric"):
            metrics.add(str(contract["metric"]))
        if contract.get("metric_label"):
            metrics.update(_mentioned_metrics(str(contract["metric_label"])))
        for container in [contract.get("summary") or {}, *(contract.get("rows") or [])]:
            if isinstance(container, dict):
                for key, value in container.items():
                    inferred = _infer_metric_from_key(str(key))
                    if inferred:
                        metrics.add(inferred)
                    if isinstance(value, str):
                        metrics.update(_mentioned_metrics(value))
    return metrics


def _infer_metric_from_key(key: str) -> str | None:
    lowered = key.lower()
    if "health_score" in lowered:
        return "health_score"
    if "risk_score" in lowered:
        return "risk_score"
    if "revenue_inventory" in lowered or "ratio" in lowered:
        return "revenue_inventory_amount_ratio"
    if "inventory_qty" in lowered or "庫存數量" in key or "庫存 qty" in lowered:
        return "inventory_qty"
    if "inventory" in lowered or "庫存" in key:
        return "inventory_amount"
    if "revenue" in lowered or "營收" in key:
        return "revenue_amount"
    return None


def _mentioned_metrics(text: str) -> set[str]:
    lowered = text.lower()
    mentioned: set[str] = set()
    for metric, hints in METRIC_LABELS.items():
        if any(hint.lower() in lowered or hint in text for hint in hints):
            mentioned.add(metric)
    return mentioned


def _metric_allowed(metric: str, allowed_metrics: set[str]) -> bool:
    if metric in allowed_metrics:
        return True
    if metric == "inventory_amount" and "inventory_qty" in allowed_metrics:
        return True
    if metric == "inventory_qty" and "inventory_amount" in allowed_metrics:
        return True
    return False


def _find_proxy_violation(text: str, canonical: dict[str, Any], evidence_dicts: list[dict[str, Any]]) -> str | None:
    metrics = {str(canonical.get("metric") or "")}
    metrics.update(str(item.get("metric") or "") for item in evidence_dicts if item.get("metric"))
    if metrics.intersection(PROXY_METRICS):
        lowered = text.lower()
        if "正式庫存週轉率" in text or "formal inventory turnover" in lowered:
            return "proxy_violation:formal_turnover_claim"
        if not any(token in lowered or token in text for token in ["proxy", "score", "scorecard"]):
            return "proxy_violation:missing_proxy_or_scorecard_label"
    return None


def _find_limitation_violation(
    writer_output: dict[str, Any],
    evidence_dicts: list[dict[str, Any]],
    deterministic_display_blocks: dict[str, Any] | None,
) -> str | None:
    required = []
    for contract in evidence_dicts:
        required.extend(str(item) for item in contract.get("limitations") or [] if item)
    if deterministic_display_blocks:
        required.extend(str(item) for item in deterministic_display_blocks.get("limitations") or [] if item)
    required = list(dict.fromkeys(required))
    if not required:
        return None
    output_limitations = [str(item) for item in writer_output.get("limitations") or [] if item]
    if not output_limitations:
        return "limitation_violation:missing_limitations"
    output_text = "\n".join(output_limitations)
    for limitation in required:
        if not _limitation_semantics_preserved(limitation, output_text):
            return f"limitation_violation:missing_limitation:{limitation[:40]}"
    return None


def _limitation_semantics_preserved(source: str, output_text: str) -> bool:
    source_lower = source.lower()
    output_lower = output_text.lower()
    if "evidencecontractbuilder does not yet support tool output" in source_lower:
        return any(token in output_lower for token in ["evidence normalization", "內部來源", "尚未納入標準", "unsupported"])
    keyword_groups = [
        ("無法直接判斷", "不能判定", "root cause", "根本原因"),
        ("proxy", "非正式周轉", "正式週轉", "正式周轉"),
        ("訂單", "出貨", "價格", "客戶", "市場需求"),
        ("資料", "coverage", "mapping", "涵蓋"),
    ]
    for group in keyword_groups:
        if any(keyword.lower() in source_lower for keyword in group):
            return any(keyword.lower() in output_lower for keyword in group)
    source_tokens = [token for token in re.findall(r"[\w\u4e00-\u9fff]+", source) if len(token) >= 2]
    if not source_tokens:
        return True
    return any(token in output_text for token in source_tokens[:3])


def _walk_values(value: Any):
    if isinstance(value, dict):
        for subvalue in value.values():
            yield from _walk_values(subvalue)
    elif isinstance(value, list):
        for subvalue in value:
            yield from _walk_values(subvalue)
    else:
        yield value


def dumps_writer_validation_context(
    canonical_task_profile: Any,
    evidence_contracts: list[Any],
    writer_output: dict[str, Any],
) -> str:
    return json.dumps(
        {
            "canonical_task_profile": _to_plain_dict(canonical_task_profile),
            "evidence_contracts": [_to_plain_dict(contract) for contract in evidence_contracts],
            "writer_output": writer_output,
        },
        ensure_ascii=False,
        indent=2,
    )
