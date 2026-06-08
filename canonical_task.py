from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class CanonicalConstraints:
    no_forecast: bool = True
    no_root_cause_claim: bool = True
    preserve_months: list[str] = field(default_factory=list)
    preserve_entities: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CanonicalTaskProfile:
    question_text: str
    task_family: str
    time_scope: dict[str, Any]
    target_entity: dict[str, Any]
    parent_entity: dict[str, Any]
    metric: str | None
    chart_type: str | None
    answer_mode: str
    constraints: CanonicalConstraints = field(default_factory=CanonicalConstraints)

    @classmethod
    def from_task_profile(cls, task_profile: Any, routing: Any | None = None) -> "CanonicalTaskProfile":
        time_scope = _canonical_time_scope(getattr(task_profile, "time_scope", {}) or {})
        target_entity = _canonical_entity(getattr(task_profile, "target_entity", {}) or {})
        parent_entity = _canonical_parent_entity(getattr(task_profile, "parent_entity", {}) or {})
        metrics = list(getattr(task_profile, "metrics", []) or [])
        question_text = str(
            getattr(routing, "question", None)
            or getattr(routing, "question_text", None)
            or getattr(task_profile, "question_text", None)
            or ""
        )
        answer_mode = str(
            getattr(routing, "answer_strategy", None)
            or getattr(task_profile, "answer_style", None)
            or getattr(task_profile, "task_family", "")
            or "query"
        )
        chart_type = _infer_chart_type(question_text, routing)
        return cls(
            question_text=question_text,
            task_family=str(getattr(task_profile, "task_family", "") or ""),
            time_scope=time_scope,
            target_entity=target_entity,
            parent_entity=parent_entity,
            metric=metrics[0] if metrics else None,
            chart_type=chart_type,
            answer_mode=answer_mode,
            constraints=CanonicalConstraints(
                no_forecast=getattr(task_profile, "task_family", None) != "forecast_unsupported",
                no_root_cause_claim=True,
                preserve_months=_preserved_months(time_scope),
                preserve_entities=_preserved_entities(target_entity, parent_entity),
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def validate_basic(self) -> tuple[bool, list[str]]:
        errors: list[str] = []
        if not self.task_family:
            errors.append("missing_task_family")
        if not self.time_scope.get("mode"):
            errors.append("missing_time_scope_mode")
        if not self.target_entity.get("dimension"):
            errors.append("missing_target_entity_dimension")
        if self.task_family != "data_quality" and self.metric is None and self.task_family != "forecast_unsupported":
            errors.append("missing_metric")
        if self.task_family == "chart_request" and not self.chart_type:
            errors.append("missing_chart_type")
        return not errors, errors


def from_task_profile(task_profile: Any, routing: Any | None = None) -> CanonicalTaskProfile:
    return CanonicalTaskProfile.from_task_profile(task_profile, routing)


def _canonical_time_scope(time_scope: dict[str, Any]) -> dict[str, Any]:
    month = time_scope.get("month") or time_scope.get("single_month")
    return {
        "mode": time_scope.get("mode") or "unspecified",
        "month": month,
        "period_a": time_scope.get("period_a"),
        "period_b": time_scope.get("period_b"),
        "start_month": time_scope.get("start_month"),
        "end_month": time_scope.get("end_month"),
        "recent_n": time_scope.get("recent_n"),
    }


def _canonical_entity(entity: dict[str, Any]) -> dict[str, Any]:
    return {
        "dimension": entity.get("dimension") or "overall",
        "scope": entity.get("scope") or ("single" if entity.get("value") else "unspecified"),
        "value": entity.get("value"),
    }


def _canonical_parent_entity(entity: dict[str, Any]) -> dict[str, Any]:
    if not entity:
        return {"dimension": None, "value": None}
    return {
        "dimension": entity.get("dimension"),
        "value": entity.get("value"),
    }


def _infer_chart_type(question_text: str, routing: Any | None) -> str | None:
    explicit = getattr(routing, "chart_type", None) if routing is not None else None
    if explicit:
        return str(explicit)
    lowered = question_text.lower()
    if "圓餅圖" in question_text or "餅圖" in question_text or "pie" in lowered:
        return "pie"
    if "長條圖" in question_text or "柱狀圖" in question_text or "條圖" in question_text or "bar" in lowered:
        return "bar"
    if "折線圖" in question_text or "線圖" in question_text or "趨勢" in question_text or "line" in lowered:
        return "line"
    if "面積圖" in question_text or "區域圖" in question_text or "area" in lowered:
        return "area"
    if any(token in question_text for token in ["圖", "圖表", "畫", "視覺化"]) or any(
        token in lowered for token in ["chart", "plot", "graph", "visual"]
    ):
        return "chart"
    return None


def _preserved_months(time_scope: dict[str, Any]) -> list[str]:
    values = [
        time_scope.get("month"),
        time_scope.get("period_a"),
        time_scope.get("period_b"),
        time_scope.get("start_month"),
        time_scope.get("end_month"),
    ]
    return [str(value) for value in values if value]


def _preserved_entities(target_entity: dict[str, Any], parent_entity: dict[str, Any]) -> list[str]:
    values = [target_entity.get("value"), parent_entity.get("value")]
    return [str(value) for value in values if value]
